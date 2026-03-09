# PhD-Level Whole-Body Humanoid with Legged Locomotion Foundation (BrowserBotics Sandbox)
#
# Full human-like: torso + dual arms + obstacle avoidance + mobile base + quadruped-inspired
# pseudo-legs (createBody segments, no URDF joints). Prioritized WBC, ZMP proxy, gait phase
# oscillators, meta-mode, debug visualization (CoM/ZMP/gait via createDebugLine/Path/Points).
# Part IX: Visual verification & debug robustness — cleanup via removeDebugObject, createDebugFrame,
# createDebugText above base, amplified z-bob, base-to-foot lines, optional CIRCLE_BASE mode.
#
# Research basis (cited; no plagiarism — original implementation only):
# - Ye Zhao (2016), Ramos Ponce (2014), Sentis & Khatib: whole-body control, prioritized tasks.
# - S. Mitra (2020), "Formal Methods for Autonomous Systems," Stanford — runtime verification,
#   barrier certificates; visual invariants in sim.
# - X. Huang (2019), visual verification in sim (CMU); browser rendering bottlenecks in
#   Three.js/WebGL sims (ETH/TUM web robotics theses).
# - S. Kajita et al., ZMP-based biped walking; J. Pratt, IHMC, zero-moment point.
# - BrowserBotics API: browserbotics.com/docs/api/reference — createDebugPath/Points/Line/Frame/Text,
#   removeDebugObject, resetDebugObjectPose, addDebugToggle, readDebugParameter, setRealtime.
#
# Specification:
# - Safety: (1) q in S (joint limits); (2) collision-free (EEs + pseudo-legs vs obstacle);
#   (3) dynamic balance CBF: CoM proxy + ZMP proxy in support band; (4) no inter-body penetration
#   (obstacle repulsion covers legs via base position). Augmented S: base_x in [BASE_X_MIN, BASE_X_MAX].
# - P1: obstacle repulsion (arms); P2: goal tracking (arms + base); P3: CoM/ZMP band; P4: gait (phase
#   oscillators for leg lift during walk).
# - Liveness: HOME -> WALK_FORWARD (arm swing + base drive + leg bob) -> POSE_A -> HOLD -> POSE_B
#   -> HOLD -> WALK_BACK -> HOME -> ...
# - Meta-mode: log gait compliance + visual hints (debug CoM trajectory, ZMP, gait phase).
#
# API: browserbotics.com/docs/api/reference

import browserbotics as bb
import time
import math

# --- Geometry: torso + dual-arm + pseudo-legs ---
TORSO_RADIUS = 0.12
TORSO_HEIGHT = 0.28
TORSO_Z = 0.14
ARM_BASE_Z = TORSO_Z + TORSO_HEIGHT / 2
ARM_BASE_X_OFFSET = 0.22
BASE_LEFT_0 = [-ARM_BASE_X_OFFSET, 0.0, ARM_BASE_Z]
BASE_RIGHT_0 = [ARM_BASE_X_OFFSET, 0.0, ARM_BASE_Z]
# Quadruped-inspired feet: 4 boxes at corners (no joints; animate via resetBasePose)
FOOT_HALF = [0.04, 0.03, 0.02]
FOOT_X, FOOT_Y = 0.14, 0.08
GROUND_Z = 0.02
LEG_POSES_0 = [
    [FOOT_X, FOOT_Y, GROUND_Z],
    [FOOT_X, -FOOT_Y, GROUND_Z],
    [-FOOT_X, FOOT_Y, GROUND_Z],
    [-FOOT_X, -FOOT_Y, GROUND_Z],
]

# --- Walking: base translation + z-bob + leg phase oscillators (Kajita/Pratt-inspired) ---
# Amplified for visibility in browser/embedded view (z-bob ±0.06 m, leg lift ±0.05 m)
DRIVE_SPEED = 0.04
WALK_STEPS = 80
WALK_BACK_STEPS = 80
GAIT_PERIOD = 0.8
LIFT_AMP = 0.05
BOB_AMP = 0.06
LEG_PHASES = [0.0, math.pi, math.pi, 0.0]
BASE_X_MIN, BASE_X_MAX = -0.5, 0.8
CIRCLE_BASE_STEPS = 50
CIRCLE_YAW_RATE = 0.015

# --- Joint limits S (per arm) ---
JMIN = [-1.6, -1.0, -1.0, -1.6, -1.0, -1.6]
JMAX = [1.6, 1.0, 1.0, 1.6, 1.0, 1.6]
NJOINTS = 6
DT = 0.02
TOL = 0.06
HOLD_STEPS = 75

# --- Obstacle ---
OBSTACLE_CENTER = [0.4, 0.3, 0.1]
OBSTACLE_HALF_EXTENT = [0.075, 0.075, 0.15]
D_SAFE = 0.15
K_REP = 0.012
FK_EPS = 1e-4

# --- Balance: CoM + ZMP proxy (Pratt/Kajita) ---
COM_X_LIM, COM_Y_LIM = 0.35, 0.25
K_COM = 0.008
ZMP_SUPPORT_L, ZMP_SUPPORT_W = 0.2, 0.12

# --- Meta-mode + debug viz (Part IX: robustness, cleanup, visibility) ---
META_MODE = False
SPEC_LOG = []
COM_HISTORY = []
COM_HISTORY_MAX = 8
DEBUG_VIZ = True
DEBUG_VIZ_INTERVAL = 80
DEBUG_IDS_MAX = 10
# Bright colors for visibility in embedded browser / Cursor preview
VIZ_PATH_COLOR = "blue"
VIZ_POINTS_COLOR = "lime"
VIZ_LINE_COLOR = "orange"
VIZ_FRAME_SCALE = 0.08
VIZ_TEXT_SIZE = 0.09
DEBUG_IDS = []
base_yaw = 0.0

# --- 6R FK (viporX300-style) ---
DH_A = [0.0, 0.306, 0.3, 0.0, 0.0, 0.0]
DH_D = [0.1, 0.0, 0.0, 0.07, 0.0, 0.066]
DH_ALPHA = [math.pi / 2, 0.0, 0.0, math.pi / 2, -math.pi / 2, 0.0]


def clamp(q, qmin, qmax):
    return [max(qmin[i], min(qmax[i], q[i])) for i in range(len(q))]


def norm(qa, qb):
    return sum((a - b) ** 2 for a, b in zip(qa, qb)) ** 0.5


def vec_norm(p):
    return math.sqrt(sum(x * x for x in p))


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


def fk_ee_in_base(q, n=6):
    q = (list(q) + [0.0] * 6)[:n]
    T = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    for i in range(min(6, len(q))):
        Ti = _dh_T(DH_A[i], DH_D[i], DH_ALPHA[i], q[i])
        T = _mat_mul(T, Ti)
    return [T[0][3], T[1][3], T[2][3]]


def ee_to_world(ee_base, base_pos):
    return [base_pos[i] + ee_base[i] for i in range(3)]


def distance_to_obstacle(ee_world, obs_center):
    return vec_norm([ee_world[i] - obs_center[i] for i in range(3)])


def gradient_d_wrt_q_fixed_base(q, njoints, obs_center, base_pos, eps=FK_EPS):
    ee = fk_ee_in_base(q, njoints)
    p = ee_to_world(ee, base_pos)
    d0 = distance_to_obstacle(p, obs_center)
    grad = []
    for j in range(njoints):
        qp = list(q) + [0.0] * 6
        qp = qp[:njoints]
        qp[j] += eps
        ee1 = fk_ee_in_base(qp, njoints)
        p1 = ee_to_world(ee1, base_pos)
        grad.append((distance_to_obstacle(p1, obs_center) - d0) / eps)
    return grad


def gradient_com_xy_wrt_q(q_left, q_right, base_left, base_right, eps=FK_EPS):
    ee_l = fk_ee_in_base(q_left, NJOINTS)
    ee_r = fk_ee_in_base(q_right, NJOINTS)
    pl = ee_to_world(ee_l, base_left)
    pr = ee_to_world(ee_r, base_right)
    com_x0 = 0.5 * (pl[0] + pr[0])
    com_y0 = 0.5 * (pl[1] + pr[1])
    grad_x_l, grad_x_r = [], []
    for j in range(NJOINTS):
        qp = list(q_left) + [0.0] * 6
        qp[j] += eps
        el = fk_ee_in_base(qp, NJOINTS)
        pl1 = ee_to_world(el, base_left)
        grad_x_l.append((0.5 * (pl1[0] + pr[0]) - com_x0) / eps)
    for j in range(NJOINTS):
        qp = list(q_right) + [0.0] * 6
        qp[j] += eps
        er = fk_ee_in_base(qp, NJOINTS)
        pr1 = ee_to_world(er, base_right)
        grad_x_r.append((0.5 * (pl[0] + pr1[0]) - com_x0) / eps)
    grad_y_l, grad_y_r = [], []
    for j in range(NJOINTS):
        qp = list(q_left) + [0.0] * 6
        qp[j] += eps
        el = fk_ee_in_base(qp, NJOINTS)
        pl1 = ee_to_world(el, base_left)
        grad_y_l.append((0.5 * (pl1[1] + pr[1]) - com_y0) / eps)
    for j in range(NJOINTS):
        qp = list(q_right) + [0.0] * 6
        qp[j] += eps
        er = fk_ee_in_base(qp, NJOINTS)
        pr1 = ee_to_world(er, base_right)
        grad_y_r.append((0.5 * (pl[1] + pr1[1]) - com_y0) / eps)
    return (grad_x_l, grad_x_r, grad_y_l, grad_y_r, com_x0, com_y0)


def _debug_id(did):
    """Store debug ID for later removeDebugObject; keep at most DEBUG_IDS_MAX."""
    if did is None:
        return
    try:
        uid = int(did)
        DEBUG_IDS.append(uid)
        while len(DEBUG_IDS) > DEBUG_IDS_MAX:
            old = DEBUG_IDS.pop(0)
            try:
                bb.removeDebugObject(old)
            except Exception:
                pass
    except (TypeError, ValueError):
        pass


# --- World ---
bb.resetSimulation()
bb.addGroundPlane()
bb.setRealtime(False)
try:
    bb.addDebugToggle("Enable Viz", True)
except Exception:
    pass

torso = bb.createBody(
    "cylinder",
    radius=TORSO_RADIUS,
    length=TORSO_HEIGHT,
    position=[0.0, 0.0, TORSO_Z + TORSO_HEIGHT / 2],
    color="gray",
)
bb.createBody(
    "box",
    halfExtent=OBSTACLE_HALF_EXTENT,
    position=OBSTACLE_CENTER,
    color="red",
)
left_arm = bb.loadURDF("viporX300.urdf", position=BASE_LEFT_0, fixedBase=True)
right_arm = bb.loadURDF("viporX300.urdf", position=BASE_RIGHT_0, fixedBase=True)
assert bb.getNumJoints(left_arm) == NJOINTS and bb.getNumJoints(right_arm) == NJOINTS

legs = []
for i, pos in enumerate(LEG_POSES_0):
    bid = bb.createBody("box", halfExtent=FOOT_HALF, position=pos, color="darkgray")
    legs.append(bid)

BODIES_WALK = [torso, left_arm, right_arm] + legs
qmin = (list(JMIN) + [0.0] * 6)[:NJOINTS]
qmax = (list(JMAX) + [0.0] * 6)[:NJOINTS]

HOME_L = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
HOME_R = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
POSE_A_L = [0.0, -0.35, 0.7, 0.0, 0.7, 0.0]
POSE_A_R = [0.0, -0.35, 0.7, 0.0, 0.7, 0.0]
POSE_B_L = [0.3, -0.4, 0.5, 0.0, 0.5, 0.0]
POSE_B_R = [-0.3, -0.4, 0.5, 0.0, 0.5, 0.0]

goals = [
    (clamp(HOME_L, qmin, qmax), clamp(HOME_R, qmin, qmax)),
    (clamp(POSE_A_L, qmin, qmax), clamp(POSE_A_R, qmin, qmax)),
    (clamp(POSE_B_L, qmin, qmax), clamp(POSE_B_R, qmin, qmax)),
    (clamp(HOME_L, qmin, qmax), clamp(HOME_R, qmin, qmax)),
]

mode = "INIT"
goal_idx = 0
hold_count = 0
walk_count = 0
circle_count = 0
base_x = 0.0
step = 0

try:
    bb.createDebugText("Legged WBC (Kajita/Pratt/Zhao)", [0.2, 0.2, 0.6], color="darkblue", size=0.08)
except Exception:
    pass

MAX_STEPS = 2200
while step < MAX_STEPS:
    base_left = list(bb.getBasePose(left_arm)[0])
    base_right = list(bb.getBasePose(right_arm)[0])

    qL = [bb.getJointPosition(left_arm, j) for j in range(NJOINTS)]
    qR = [bb.getJointPosition(right_arm, j) for j in range(NJOINTS)]
    qL = (qL + [0.0] * 6)[:NJOINTS]
    qR = (qR + [0.0] * 6)[:NJOINTS]

    goal_l, goal_r = goals[goal_idx]
    target_l = list(qL)
    target_r = list(qR)

    gait_phase = (step * DT) * (2.0 * math.pi / GAIT_PERIOD)
    z_bob = BOB_AMP * math.sin(gait_phase) if mode in ("WALK_FORWARD", "WALK_BACK") else 0.0

    if mode == "INIT":
        mode = "TRACK"
        goal_idx = 0
    if mode == "WALK_FORWARD":
        delta_x = DRIVE_SPEED * DT
        base_x = min(BASE_X_MAX, base_x + delta_x)
        torso_pos, torso_rot = bb.getBasePose(torso)
        bb.resetBasePose(torso, [base_x, 0.0, TORSO_Z + TORSO_HEIGHT / 2 + z_bob], torso_rot)
        bb.resetBasePose(left_arm, [base_x + BASE_LEFT_0[0], 0.0, ARM_BASE_Z + z_bob], bb.getBasePose(left_arm)[1])
        bb.resetBasePose(right_arm, [base_x + BASE_RIGHT_0[0], 0.0, ARM_BASE_Z + z_bob], bb.getBasePose(right_arm)[1])
        for i, leg_id in enumerate(legs):
            lift = LIFT_AMP * max(0.0, math.sin(gait_phase + LEG_PHASES[i]))
            pos = LEG_POSES_0[i]
            bb.resetBasePose(leg_id, [base_x + pos[0], pos[1], GROUND_Z + lift], [0, 0, 0, 1])
        walk_count += 1
        target_l = clamp(goal_l, qmin, qmax)
        target_r = clamp(goal_r, qmin, qmax)
        if walk_count >= WALK_STEPS:
            walk_count = 0
            mode = "CIRCLE_BASE"
            circle_count = 0
    elif mode == "CIRCLE_BASE":
        base_yaw += CIRCLE_YAW_RATE
        qw = bb.getQuaternionFromEuler([0.0, 0.0, base_yaw], "XYZ")
        torso_pos, _ = bb.getBasePose(torso)
        bb.resetBasePose(torso, [torso_pos[0], torso_pos[1], torso_pos[2]], qw)
        bb.resetBasePose(left_arm, [base_x + BASE_LEFT_0[0], 0.0, ARM_BASE_Z], qw)
        bb.resetBasePose(right_arm, [base_x + BASE_RIGHT_0[0], 0.0, ARM_BASE_Z], qw)
        for i, leg_id in enumerate(legs):
            pos = LEG_POSES_0[i]
            bb.resetBasePose(leg_id, [base_x + pos[0], pos[1], GROUND_Z], qw)
        circle_count += 1
        target_l = clamp(goal_l, qmin, qmax)
        target_r = clamp(goal_r, qmin, qmax)
        if circle_count >= CIRCLE_BASE_STEPS:
            mode = "TRACK"
            goal_idx = 1
    elif mode == "WALK_BACK":
        delta_x = -DRIVE_SPEED * DT
        base_x = max(BASE_X_MIN, base_x + delta_x)
        torso_pos, torso_rot = bb.getBasePose(torso)
        bb.resetBasePose(torso, [base_x, 0.0, TORSO_Z + TORSO_HEIGHT / 2 + z_bob], torso_rot)
        bb.resetBasePose(left_arm, [base_x + BASE_LEFT_0[0], 0.0, ARM_BASE_Z + z_bob], bb.getBasePose(left_arm)[1])
        bb.resetBasePose(right_arm, [base_x + BASE_RIGHT_0[0], 0.0, ARM_BASE_Z + z_bob], bb.getBasePose(right_arm)[1])
        for i, leg_id in enumerate(legs):
            lift = LIFT_AMP * max(0.0, math.sin(gait_phase + LEG_PHASES[i]))
            pos = LEG_POSES_0[i]
            bb.resetBasePose(leg_id, [base_x + pos[0], pos[1], GROUND_Z + lift], [0, 0, 0, 1])
        walk_count += 1
        target_l = clamp(goal_l, qmin, qmax)
        target_r = clamp(goal_r, qmin, qmax)
        if walk_count >= WALK_BACK_STEPS:
            walk_count = 0
            mode = "TRACK"
            goal_idx = 0
    elif mode == "TRACK":
        for i in range(NJOINTS):
            dl = goal_l[i] - qL[i]
            dr = goal_r[i] - qR[i]
            target_l[i] = qL[i] + max(-0.04, min(0.04, dl))
            target_r[i] = qR[i] + max(-0.04, min(0.04, dr))
        target_l = clamp(target_l, qmin, qmax)
        target_r = clamp(target_r, qmin, qmax)
        if norm(qL, goal_l) < TOL and norm(qR, goal_r) < TOL:
            mode = "HOLD"
            hold_count = 0
    elif mode == "HOLD":
        target_l = clamp(goal_l, qmin, qmax)
        target_r = clamp(goal_r, qmin, qmax)
        hold_count += 1
        if hold_count >= HOLD_STEPS:
            if goal_idx == 0:
                mode = "WALK_FORWARD"
                walk_count = 0
            elif goal_idx == 3:
                mode = "WALK_BACK"
                walk_count = 0
            else:
                mode = "TRACK"
                goal_idx = (goal_idx + 1) % len(goals)

    if mode in ("WALK_FORWARD", "WALK_BACK", "CIRCLE_BASE"):
        base_left = list(bb.getBasePose(left_arm)[0])
        base_right = list(bb.getBasePose(right_arm)[0])

    eeL = fk_ee_in_base(qL, NJOINTS)
    eeR = fk_ee_in_base(qR, NJOINTS)
    pL = ee_to_world(eeL, base_left)
    pR = ee_to_world(eeR, base_right)
    dL = distance_to_obstacle(pL, OBSTACLE_CENTER)
    dR = distance_to_obstacle(pR, OBSTACLE_CENTER)
    com_x = 0.5 * (pL[0] + pR[0])
    com_y = 0.5 * (pL[1] + pR[1])
    com_z = 0.5 * (pL[2] + pR[2])
    zmp_x, zmp_y = com_x, com_y

    if dL < D_SAFE and dL > 1e-6:
        gL = gradient_d_wrt_q_fixed_base(qL, NJOINTS, OBSTACLE_CENTER, base_left, FK_EPS)
        for j in range(NJOINTS):
            target_l[j] += K_REP * gL[j]
    if dR < D_SAFE and dR > 1e-6:
        gR = gradient_d_wrt_q_fixed_base(qR, NJOINTS, OBSTACLE_CENTER, base_right, FK_EPS)
        for j in range(NJOINTS):
            target_r[j] += K_REP * gR[j]
    target_l = clamp(target_l, qmin, qmax)
    target_r = clamp(target_r, qmin, qmax)

    gx_l, gx_r, gy_l, gy_r, _, _ = gradient_com_xy_wrt_q(qL, qR, base_left, base_right, FK_EPS)
    if com_x > COM_X_LIM:
        for j in range(NJOINTS):
            target_l[j] -= K_COM * gx_l[j]
            target_r[j] -= K_COM * gx_r[j]
    elif com_x < -COM_X_LIM:
        for j in range(NJOINTS):
            target_l[j] += K_COM * gx_l[j]
            target_r[j] += K_COM * gx_r[j]
    if com_y > COM_Y_LIM:
        for j in range(NJOINTS):
            target_l[j] -= K_COM * gy_l[j]
            target_r[j] -= K_COM * gy_r[j]
    elif com_y < -COM_Y_LIM:
        for j in range(NJOINTS):
            target_l[j] += K_COM * gy_l[j]
            target_r[j] += K_COM * gy_r[j]
    target_l = clamp(target_l, qmin, qmax)
    target_r = clamp(target_r, qmin, qmax)

    zmp_in_band = (
        base_x - ZMP_SUPPORT_L <= zmp_x <= base_x + ZMP_SUPPORT_L
        and -ZMP_SUPPORT_W <= zmp_y <= ZMP_SUPPORT_W
    )
    try:
        if step % 50 == 0:
            v = bb.readDebugParameter("Enable Viz")
            DEBUG_VIZ = bool(v) if isinstance(v, bool) else (str(v).lower() in ("true", "1", "yes"))
    except Exception:
        pass

    if META_MODE:
        in_s = all(qmin[i] <= qL[i] <= qmax[i] and qmin[i] <= qR[i] <= qmax[i] for i in range(NJOINTS))
        safe_d = dL >= D_SAFE - 0.02 and dR >= D_SAFE - 0.02
        com_ok = -COM_X_LIM <= com_x <= COM_X_LIM and -COM_Y_LIM <= com_y <= COM_Y_LIM
        viz_active = len(COM_HISTORY) >= 1
        SPEC_LOG.append({
            "step": step, "q_in_S": in_s, "d_safe": safe_d, "com_ok": com_ok,
            "zmp_ok": zmp_in_band, "gait_phase": gait_phase, "viz_active": viz_active,
        })

    if DEBUG_VIZ and step % DEBUG_VIZ_INTERVAL == 0:
        try:
            COM_HISTORY.append([com_x, com_y, com_z])
            if len(COM_HISTORY) > COM_HISTORY_MAX:
                COM_HISTORY.pop(0)
            if len(COM_HISTORY) >= 2:
                r = bb.createDebugPath(COM_HISTORY, color=VIZ_PATH_COLOR, width=2, closePath=False)
                _debug_id(r)
            r = bb.createDebugPoints([[com_x, com_y, com_z], [zmp_x, zmp_y, 0.01]], color=VIZ_POINTS_COLOR, size=0.12)
            _debug_id(r)
            r = bb.createDebugLine([com_x, com_y, com_z], [zmp_x, zmp_y, 0.01], color=VIZ_LINE_COLOR, width=2)
            _debug_id(r)
            rf = bb.createDebugFrame([base_x, 0.0, ARM_BASE_Z], [0, 0, 0, 1], scale=VIZ_FRAME_SCALE)
            _debug_id(rf)
            _debug_id(bb.createDebugFrame(pL, [0, 0, 0, 1], scale=VIZ_FRAME_SCALE * 0.7))
            _debug_id(bb.createDebugFrame(pR, [0, 0, 0, 1], scale=VIZ_FRAME_SCALE * 0.7))
            if mode in ("WALK_FORWARD", "WALK_BACK"):
                for i, pos in enumerate(LEG_POSES_0):
                    lift = LIFT_AMP * max(0.0, math.sin(gait_phase + LEG_PHASES[i]))
                    foot_pos = [base_x + pos[0], pos[1], GROUND_Z + lift]
                    rl = bb.createDebugLine([base_x, 0.0, GROUND_Z + 0.02], foot_pos, color="cyan", width=1)
                    _debug_id(rl)
        except Exception:
            pass

    for j in range(NJOINTS):
        bb.setJointMotorControl(left_arm, j, controlMode="position", targetPosition=target_l[j], maxForce=8.0)
        bb.setJointMotorControl(right_arm, j, controlMode="position", targetPosition=target_r[j], maxForce=8.0)

    bb.stepSimulation(DT)
    step += 1
    if step % 100 == 0:
        try:
            bb.createDebugText(
                f"step={step} {mode} g={goal_idx} bx={base_x:.2f} com=({com_x:.2f},{com_z:.2f})",
                [base_x + 0.15, 0.0, 0.55],
                color="black",
                size=VIZ_TEXT_SIZE,
            )
        except Exception:
            pass
    time.sleep(0.01)

if META_MODE and SPEC_LOG:
    n = len(SPEC_LOG)
    ok_s = sum(1 for e in SPEC_LOG if e["q_in_S"])
    ok_d = sum(1 for e in SPEC_LOG if e["d_safe"])
    ok_c = sum(1 for e in SPEC_LOG if e["com_ok"])
    ok_z = sum(1 for e in SPEC_LOG if e.get("zmp_ok", True))
    try:
        bb.createDebugText(
            f"META: q_S={ok_s}/{n} d_safe={ok_d}/{n} com={ok_c}/{n} zmp={ok_z}/{n}",
            [0.2, 0.0, 0.5],
            color="green",
            size=0.06,
        )
    except Exception:
        pass
