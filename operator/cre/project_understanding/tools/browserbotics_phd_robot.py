# PhD-Level Specification-Driven Robot Controller with Obstacle Awareness (BrowserBotics Sandbox)
# Foundation: invariant safe set S (joint limits) + liveness (state machine) + deterministic fixed-step sim.
# Extension: collision-free motion via distance-based repulsion (avoid set / soft barrier).
# Research basis: formal methods (discrete abstraction, LTL/STL), safe controller synthesis (CBFs),
#   potential field obstacle avoidance (Khatib, IJRR 1986), control barrier functions (Ames et al.),
#   reachability/avoid sets (TUM, eTheses). This implementation is original; no code copied from other sources.
# Refs: Khatib (1986) Real-time obstacle avoidance for manipulators; Ames et al. CBFs;
#       formal verification (eTheses), LTL/STL (MPI-SWS, UMN). API: browserbotics.com/docs/api/reference

import browserbotics as bb
import time
import math

# --- Specification (our formulation) ---
# Safety: (1) q(t) in safe set S (joint limits) for all t; (2) end-effector / links avoid obstacle (distance >= d_safe).
# Liveness: system eventually reaches goal configuration and holds (HOLD mode); same four goals (or path around obstacle).

# Conservative joint limits (rad) for viporX300-style arm; clamp all targets to S.
JMIN = [-1.6, -1.0, -1.0, -1.6, -1.0, -1.6]
JMAX = [1.6, 1.0, 1.0, 1.6, 1.0, 1.6]
DT = 0.02
TOL = 0.05
HOLD_STEPS = 75  # hold ~1.5 s at 50 Hz stepping

# Obstacle: static box in workspace; repulsion when EE within D_SAFE (soft barrier).
OBSTACLE_CENTER = [0.4, 0.3, 0.1]
OBSTACLE_HALF_EXTENT = [0.075, 0.075, 0.15]  # 0.15 x 0.15 x 0.3 m box
D_SAFE = 0.15   # min desired distance (m); repulsion active when d < D_SAFE
K_REP = 0.015   # repulsion gain (nudge target in direction that increases d)
FK_EPS = 1e-4   # finite-difference step for gradient of d w.r.t. q

def clamp(q, qmin, qmax):
    return [max(qmin[i], min(qmax[i], q[i])) for i in range(len(q))]

def norm(qa, qb):
    return sum((a - b) ** 2 for a, b in zip(qa, qb)) ** 0.5

def vec_norm(p):
    return math.sqrt(sum(x * x for x in p))

# --- Simple 6R forward kinematics (approximate for viporX300-style arm) ---
# Standard DH: a, d, alpha; theta = q[i]. T_i = Rz(theta)*Tz(d)*Tx(a)*Rx(alpha). EE = T_0_6[:3,3].
# Plausible params for 6R arm (waist, shoulder, elbow, wrist 1–3) so EE is in workspace near obstacle.
DH_A = [0.0, 0.306, 0.3, 0.0, 0.0, 0.0]       # link lengths (m), ViperX-300 style
DH_D = [0.1, 0.0, 0.0, 0.07, 0.0, 0.066]
DH_ALPHA = [math.pi / 2, 0.0, 0.0, math.pi / 2, -math.pi / 2, 0.0]

def _dh_T(a, d, alpha, theta):
    ct, st = math.cos(theta), math.sin(theta)
    ca, sa = math.cos(alpha), math.sin(alpha)
    return [
        [ct, -st * ca, st * sa, a * ct],
        [st, ct * ca, -ct * sa, a * st],
        [0.0, sa, ca, d],
        [0.0, 0.0, 0.0, 1.0],
    ]

def _mat_mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

def fk_ee_position(q, njoints=6):
    """Return end-effector position [x, y, z] from joint angles q (rad). Simple 6R FK."""
    q = (list(q) + [0.0] * 6)[:njoints]
    T = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    for i in range(min(6, len(q))):
        Ti = _dh_T(DH_A[i], DH_D[i], DH_ALPHA[i], q[i])
        T = _mat_mul(T, Ti)
    return [T[0][3], T[1][3], T[2][3]]

def distance_to_obstacle(ee_pos, obs_center):
    return vec_norm([ee_pos[i] - obs_center[i] for i in range(3)])

def gradient_d_wrt_q(robot, q, njoints, obs_center, eps=FK_EPS):
    """Numerical gradient of d (distance EE to obstacle) w.r.t. q. Returns list of length njoints."""
    d0 = distance_to_obstacle(fk_ee_position(q, njoints), obs_center)
    grad = []
    for j in range(njoints):
        qp = list(q) + [0.0] * 6
        qp = qp[:njoints]
        qp[j] += eps
        d1 = distance_to_obstacle(fk_ee_position(qp, njoints), obs_center)
        grad.append((d1 - d0) / eps)
    return grad

# --- World ---
bb.resetSimulation()
bb.addGroundPlane()
bb.setRealtime(False)

# Static obstacle: box at OBSTACLE_CENTER, visible in 3D view
bb.createBody(
    "box",
    halfExtent=OBSTACLE_HALF_EXTENT,
    position=OBSTACLE_CENTER,
    color="red",
)

robot = bb.loadURDF("viporX300.urdf", fixedBase=True)
njoints = bb.getNumJoints(robot)

qmin = (list(JMIN) + [0.0] * 6)[:njoints]
qmax = (list(JMAX) + [0.0] * 6)[:njoints]

# Goals (within safe set S); same four as before
goals = [
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0, -0.4, 0.8, 0.0, 0.8, 0.0],
    [0.5, -0.3, 0.6, 0.0, 0.6, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
]
goals = [clamp(g, qmin, qmax) for g in goals]

mode = "INIT"
goal_idx = 0
hold_count = 0
step = 0

try:
    bb.createDebugText("Spec+obstacle (Khatib/CBF-inspired)", [0.2, 0.2, 0.5], color="darkblue", size=0.08)
except Exception:
    pass

MAX_STEPS = 800
while step < MAX_STEPS:
    q = [bb.getJointPosition(robot, j) for j in range(njoints)]
    q = (q + [0.0] * 6)[:njoints]

    target = list(q)
    if mode == "INIT":
        mode = "TRACK"
        goal_idx = 0
    if mode == "TRACK":
        g = goals[goal_idx]
        for i in range(njoints):
            diff = g[i] - q[i]
            target[i] = q[i] + max(-0.05, min(0.05, diff))
        target = clamp(target, qmin, qmax)
        if norm(q, goals[goal_idx]) < TOL:
            mode = "HOLD"
            hold_count = 0
    elif mode == "HOLD":
        target = clamp(goals[goal_idx], qmin, qmax)
        hold_count += 1
        if hold_count >= HOLD_STEPS:
            goal_idx = (goal_idx + 1) % len(goals)
            mode = "TRACK"

    # Obstacle avoidance: soft barrier / potential-field style (Khatib-inspired)
    ee = fk_ee_position(q, njoints)
    d = distance_to_obstacle(ee, OBSTACLE_CENTER)
    if d < D_SAFE and d > 1e-6:
        grad_d = gradient_d_wrt_q(robot, q, njoints, OBSTACLE_CENTER, FK_EPS)
        for j in range(njoints):
            target[j] = target[j] + K_REP * grad_d[j]
        target = clamp(target, qmin, qmax)

    for j in range(njoints):
        bb.setJointMotorControl(robot, j, controlMode="position", targetPosition=target[j], maxForce=8.0)

    bb.stepSimulation(DT)
    step += 1
    if step % 50 == 0:
        try:
            bb.createDebugText(f"mode={mode} goal={goal_idx} d={d:.2f}", [0.2, 0.0, 0.45], color="black", size=0.06)
        except Exception:
            pass
    time.sleep(0.01)
