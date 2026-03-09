"""
BrowserBotics Sandbox — PhD-level build: Phase-coupled oscillator lattice
(Morphological computation / Kuramoto-style synchronization in a physics sim)

Research frame: Emergent synchronization in a 2D lattice of coupled oscillators
with forces mapped from phase. Not copying existing builds; uses createBody,
getBasePose, applyExternalForce, stepSimulation, and debug visualization.

Paste this entire file into the BrowserBotics sandbox code editor and click Run.
"""

import browserbotics as bb
import math

# --- Parameters ---
N = 5                    # grid NxN
spacing = 0.6
radius = 0.12
K = 2.0                   # Kuramoto coupling strength
omega0 = 1.0              # base frequency
F_mag = 8.0               # force magnitude from phase
steps = 400
dt = 0.02
trail_len = 80            # trajectory history for debug path

# --- Setup ---
bb.resetSimulation()
bb.addGroundPlane(height=0.0)
bb.setGravity(0, 0, -9.81)
bb.setRealtime(False)

# Create N*N spheres in a grid
body_ids = []
phases = []
for i in range(N):
    for j in range(N):
        x = (i - (N - 1) / 2) * spacing
        y = (j - (N - 1) / 2) * spacing
        bid = bb.createBody(
            "sphere",
            radius=radius,
            position=[x, y, radius + 0.02],
            mass=0.5,
            color="blue",
        )
        body_ids.append(bid)
        phases.append(2 * math.pi * (i + j) / (2 * N))  # initial phase gradient

n_bodies = len(body_ids)
trails = [[] for _ in range(min(4, n_bodies))]  # store trails for first 4 bodies

def get_grid_index(idx):
    return (idx // N, idx % N)

def neighbor_indices(idx):
    i, j = get_grid_index(idx)
    out = []
    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        ni, nj = i + di, j + dj
        if 0 <= ni < N and 0 <= nj < N:
            out.append(ni * N + nj)
    return out

# --- Main loop: Kuramoto-like coupling + force injection ---
for step in range(steps):
    # 1) Get current positions (for neighbor coupling we use phases only for simplicity)
    positions = []
    for idx, bid in enumerate(body_ids):
        pos, _ = bb.getBasePose(bid)
        positions.append(pos)
        # 2) Kuramoto d(theta)/dt = omega + K * sum_j sin(theta_j - theta_i)
        neighbors = neighbor_indices(idx)
        dphase = omega0 * 0.1
        for nidx in neighbors:
            dphase += (K / max(len(neighbors), 1)) * math.sin(phases[nidx] - phases[idx])
        phases[idx] += dphase * dt
        phases[idx] = phases[idx] % (2 * math.pi)
        # 3) Apply horizontal force proportional to sin(phase) — drives motion
        fx = F_mag * math.sin(phases[idx])
        fy = F_mag * math.cos(phases[idx] * 0.7)
        bb.applyExternalForce(bid, 0, [fx, fy, 0], [0, 0, 0])

    bb.stepSimulation(dt)

    # Store trail for first 4 bodies
    for t in range(min(4, n_bodies)):
        bid = body_ids[t]
        pos, _ = bb.getBasePose(bid)
        trails[t].append([pos[0], pos[1], pos[2] + 0.15])
        if len(trails[t]) > trail_len:
            trails[t].pop(0)

# --- Visualization: trajectories and final state text ---
bb.createDebugText("Phase-coupled lattice (Kuramoto-style)", [0, 0, 1.2], color="black", size=0.08)
for t, trail in enumerate(trails):
    if len(trail) >= 2:
        bb.createDebugPath(trail, color="red" if t == 0 else "green", width=2, closePath=False)
# Optional: coordinate frame at origin (omit if API differs in sandbox)
# bb.createDebugFrame([0, 0, 0.5], [0, 0, 0, 1], 0.2)
