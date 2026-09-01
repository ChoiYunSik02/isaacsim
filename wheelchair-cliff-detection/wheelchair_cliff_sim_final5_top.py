# SPDX-License-Identifier: Apache-2.0
# Smart Wheelchair — VL53L8CX 8×8 ToF 낙상 감지 + 우회 네비게이션 (Final5 HUD EN-only / TOP-CLIFF)
#
# ✅ 요구사항 반영
# 1) 터미널(콘솔) 로그: 한글 유지
# 2) HUD(UI 창): 영어만 사용(한글 사용 금지) → ??? 깨짐 방지
# 3) HUD 8×8이 잘리는 문제: 도킹 금지 + 스크롤 프레임 적용
# 4) 숫자(mm) 표시 ON
# 5) 색상 규칙:
#    - HUD 화면 상단 2행 (배열 Row 6~7) : 초록/노랑/주황/빨강 허용 → 낙상 판정 구역
#    - HUD 화면 하단 6행 (배열 Row 0~5) : 초록/노랑만 (주황/빨강 금지) → 원거리 모니터링
#    - CLIFF 판정 시 상단 2행의 해당 L/C/R 영역만 빨강 강제
#    ※ 판정에 쓰이는 배열 인덱스(BOTTOM_ROWS=[6,7])와 판정 로직은 기존과 동일하며,
#      HUD 그리드를 "그리는 순서"만 위아래로 뒤집어 화면 상단에 낙상 판정 구역이 보이도록 수정함.
#
# 실행:
#   C:\isaacsim\python.bat C:\issacsim_project\wheelchair_cliff_sim_final5_top.py

import argparse, math
import numpy as np
from isaacsim import SimulationApp

parser = argparse.ArgumentParser()
parser.add_argument("--test", default=False, action="store_true")
args, unknown = parser.parse_known_args()

simulation_app = SimulationApp({"headless": False, "width": 1280, "height": 720})

import omni.physx, omni.usd, carb
import omni.ui as ui
from isaacsim.core.api import World
from isaacsim.core.api.objects import GroundPlane
from isaacsim.core.utils.viewports import set_camera_view
from isaacsim.robot.wheeled_robots.robots import WheeledRobot
from isaacsim.robot.wheeled_robots.controllers.differential_controller import DifferentialController
from isaacsim.storage.native import get_assets_root_path
from pxr import Gf, UsdGeom, UsdLux, UsdPhysics


# ─────────────────────────────────────────────
# 0) HUD 설정 (영어만)
# ─────────────────────────────────────────────
HUD_ENABLED = True
HUD_SCALE = 1.0
HUD_OPACITY = 0.82
HUD_SHOW_NUMBERS = True  # ✅ 숫자(mm) 표시

# HUD 도킹 방지 + 스크롤 지원
HUD_NO_DOCKING = True
HUD_START_POS = (980, 250)
HUD_START_SIZE = (380, 340)

# 히트맵 색상 기준(mm)
MM_GREEN  = 250
MM_YELLOW = 500
MM_ORANGE = 900

COLOR_BG = ui.color(0.0, 0.0, 0.0, HUD_OPACITY)
COLOR_TEXT = ui.color(1.0, 1.0, 1.0, 1.0)
COLOR_OK = ui.color(0.30, 0.95, 0.45, 1.0)
COLOR_WARN = ui.color(1.00, 0.75, 0.10, 1.0)
COLOR_ORANGE = ui.color(1.00, 0.45, 0.10, 1.0)
COLOR_DANGER = ui.color(1.00, 0.25, 0.25, 1.0)
COLOR_MISS = ui.color(0.10, 0.10, 0.10, 1.0)
COLOR_BORDER = ui.color(1.0, 1.0, 1.0, 0.25)
# (구) COLOR_BOTTOMROW_BORDER → 낙상 판정 구역이 화면 상단으로 이동했으므로 이름도 갱신
COLOR_CLIFFROW_BORDER = ui.color(0.90, 0.90, 0.15, 0.75)


# ─────────────────────────────────────────────
# 1) 환경/주행 파라미터
# ─────────────────────────────────────────────
PLATFORM_H   = 0.50
PLATFORM_LEN = 3.5
PLATFORM_W   = 2.0
CLIFF_X      = PLATFORM_LEN
EDGE_GUARD_X = CLIFF_X - 0.20

STAIR_COUNT  = 4
STAIR_W      = 0.35
STAIR_H      = PLATFORM_H / STAIR_COUNT

BYPASS_Y0        = PLATFORM_W / 2
BYPASS_Y1        = BYPASS_Y0 + 1.8
BYPASS_Y_TARGET  = BYPASS_Y0 + 0.8
BYPASS_RAMP_END  = CLIFF_X + 2.5

PHYSICS_DT = 1.0/60.0
STOP_SEC   = 0.4
REVERSE_SEC= 1.2
STOP_STEPS    = int(STOP_SEC / PHYSICS_DT)
REVERSE_STEPS = int(REVERSE_SEC / PHYSICS_DT)

BASE_SPEED    = 0.20
REVERSE_SPEED = 0.10
TURN_RATE     = math.pi/4
SCAN_RATE     = math.pi/5

LOG_INTERVAL_SEC = 3.0


# ─────────────────────────────────────────────
# 2) VL53L8CX 8×8 ToF 파라미터
# ─────────────────────────────────────────────
TOF_ROWS = 8
TOF_COLS = 8
TOF_FOV_H_DEG = 45.0
TOF_FOV_V_DEG = 45.0

TOF_HZ = 15.0
TOF_DT = 1.0 / TOF_HZ

TOF_MIN_M = 0.02
TOF_MAX_M = 4.00

SENSOR_LOCAL_OFFSET = np.array([0.18, 0.00, 0.05], dtype=np.float64)

# ✅ 패치3 성공값 유지: 아래(-Z)로 향하도록 +45°
SENSOR_MOUNT_PITCH_DEG = +45.0

APPLY_ZONE_FLIP = True

ENABLE_NOISE = True
NOISE_SEED = 7
rng = np.random.default_rng(NOISE_SEED)


# ─────────────────────────────────────────────
# 3) 낙상 판정 (배열 Row 6~7 / HUD 화면 표시는 상단 2행)
# ─────────────────────────────────────────────
BOTTOM_ROWS = [6, 7]
L_COLS = [0, 1, 2]
C_COLS = [3, 4]
R_COLS = [5, 6, 7]

baseline = {"floor_m": None}
BASELINE_ALPHA = 0.05

MIN_HIT_RATIO = 0.50
RELATIVE_JUMP = 1.8
ABS_CLIFF_M   = 1.20

SAFE_NEED = 6
MAX_SCAN_RAD = math.pi


# ─────────────────────────────────────────────
# 4) 상태 (콘솔=한글, HUD=영어)
# ─────────────────────────────────────────────
S_FORWARD   = "FORWARD"
S_STOP      = "STOP"
S_REVERSE   = "REVERSE"
S_SCANNING  = "SCANNING"
S_TO_BYPASS = "TO_BYPASS"
S_TURN_FWD  = "TURN_FWD"
S_DESCEND   = "DESCEND"
S_DONE      = "DONE"

# 콘솔(한글)
STATE_KO = {
    S_FORWARD:   "직진",
    S_STOP:      "정지",
    S_REVERSE:   "후진",
    S_SCANNING:  "스캔",
    S_TO_BYPASS: "우회 복도 진입",
    S_TURN_FWD:  "전방 정렬",
    S_DESCEND:   "경사로 하강",
    S_DONE:      "완료",
}
TAG_KO = {"INIT":"초기", "STATE_CHANGE":"상태변경", "HEARTBEAT":"주기"}

# HUD(영어)
STATE_EN = {
    S_FORWARD:   "FORWARD",
    S_STOP:      "STOP",
    S_REVERSE:   "REVERSE",
    S_SCANNING:  "SCAN",
    S_TO_BYPASS: "BYPASS",
    S_TURN_FWD:  "ALIGN",
    S_DESCEND:   "DESCEND",
    S_DONE:      "DONE",
}


# ─────────────────────────────────────────────
# 5) 월드/조명/카메라
# ─────────────────────────────────────────────
my_world = World(stage_units_in_meters=1.0)
stage = omni.usd.get_context().get_stage()

UsdLux.DistantLight.Define(stage, "/World/Sun").CreateIntensityAttr(800)
dome = UsdLux.DomeLight.Define(stage, "/World/Dome")
dome.CreateIntensityAttr(400)
dome.CreateColorAttr(Gf.Vec3f(0.87, 0.91, 1.0))

set_camera_view(
    eye=np.array([1.0, -6.5, 5.5]),
    target=np.array([4.0, 1.2, 0.3]),
    camera_prim_path="/OmniverseKit_Persp",
)

GroundPlane(prim_path="/World/GroundPlane", z_position=0.0)


# ─────────────────────────────────────────────
# 6) 메시 생성 유틸
# ─────────────────────────────────────────────
def _coll(prim):
    UsdPhysics.CollisionAPI.Apply(prim)
    mc = UsdPhysics.MeshCollisionAPI.Apply(prim)
    mc.CreateApproximationAttr("none")

def make_box(path, x0,x1,y0,y1,z0,z1, color, collision=True):
    v = [Gf.Vec3f(x0,y0,z0), Gf.Vec3f(x1,y0,z0),
         Gf.Vec3f(x1,y1,z0), Gf.Vec3f(x0,y1,z0),
         Gf.Vec3f(x0,y0,z1), Gf.Vec3f(x1,y0,z1),
         Gf.Vec3f(x1,y1,z1), Gf.Vec3f(x0,y1,z1)]
    m = UsdGeom.Mesh.Define(stage, path)
    m.CreatePointsAttr(v)
    m.CreateFaceVertexCountsAttr([4]*6)
    m.CreateFaceVertexIndicesAttr([0,3,2,1, 4,5,6,7, 0,1,5,4, 3,7,6,2, 0,4,7,3, 1,2,6,5])
    m.CreateDoubleSidedAttr(True)
    m.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    if collision:
        _coll(m.GetPrim())

def make_ramp(path, x0,x1,y0,y1,z_hi,z_lo, color, collision=True):
    v = [Gf.Vec3f(x0,y0,0),    Gf.Vec3f(x1,y0,0),
         Gf.Vec3f(x1,y1,0),    Gf.Vec3f(x0,y1,0),
         Gf.Vec3f(x0,y0,z_hi), Gf.Vec3f(x1,y0,z_lo),
         Gf.Vec3f(x1,y1,z_lo), Gf.Vec3f(x0,y1,z_hi)]
    m = UsdGeom.Mesh.Define(stage, path)
    m.CreatePointsAttr(v)
    m.CreateFaceVertexCountsAttr([4]*6)
    m.CreateFaceVertexIndicesAttr([3,2,1,0, 4,5,6,7, 0,1,5,4, 7,6,2,3, 3,0,4,7, 1,2,6,5])
    m.CreateDoubleSidedAttr(True)
    m.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    if collision:
        _coll(m.GetPrim())


# ─────────────────────────────────────────────
# 7) 환경 구성 (Marker 없음)
# ─────────────────────────────────────────────
make_box("/World/Platform/Body",
    0.0, CLIFF_X, -PLATFORM_W/2, PLATFORM_W/2, 0.0, PLATFORM_H,
    (0.80, 0.80, 0.82), collision=True)

make_box("/World/Platform/CurbL",
    0.0, CLIFF_X, -PLATFORM_W/2, -PLATFORM_W/2 + 0.05,
    PLATFORM_H, PLATFORM_H + 0.02,
    (0.92, 0.92, 0.92), collision=True)

stair_c = [(0.70,0.70,0.72),(0.65,0.65,0.67),(0.60,0.60,0.62),(0.55,0.55,0.57)]
for i in range(STAIR_COUNT):
    top_h = PLATFORM_H - (i+1)*STAIR_H
    make_box(f"/World/Stairs/Step{i}",
        CLIFF_X+i*STAIR_W, CLIFF_X+(i+1)*STAIR_W,
        -PLATFORM_W/2, BYPASS_Y0,
        0.0, max(0.0, top_h),
        stair_c[i], collision=True)

make_box("/World/Bypass/Corridor",
    0.0, CLIFF_X, BYPASS_Y0, BYPASS_Y1, 0.0, PLATFORM_H,
    (0.50, 0.72, 0.50), collision=True)

make_ramp("/World/Bypass/Ramp",
    CLIFF_X, BYPASS_RAMP_END, BYPASS_Y0, BYPASS_Y1,
    PLATFORM_H, 0.0, (0.45, 0.65, 0.45), collision=True)


# ─────────────────────────────────────────────
# 8) JetBot
# ─────────────────────────────────────────────
assets_root = get_assets_root_path()
if assets_root is None:
    carb.log_error("에셋 경로를 찾을 수 없습니다")
    simulation_app.close()
    raise SystemExit(1)

my_jetbot = my_world.scene.add(WheeledRobot(
    prim_path="/World/Jetbot", name="my_jetbot",
    wheel_dof_names=["left_wheel_joint", "right_wheel_joint"],
    create_robot=True,
    usd_path=assets_root + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd",
    position=np.array([0.4, 0.0, PLATFORM_H + 0.05]),
))
my_ctrl = DifferentialController(name="diff_ctrl", wheel_radius=0.03, wheel_base=0.1125)


# ─────────────────────────────────────────────
# 9) 쿼터니언/회전 유틸 (xyzw/wxyz 자동 감지)
# ─────────────────────────────────────────────
def normalize_quat(q):
    q = np.array(q, dtype=np.float64)
    n = np.linalg.norm(q)
    if n < 1e-12:
        return np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)
    return q / n

def quat_to_wxyz(q):
    q = normalize_quat(q)
    if abs(q[3]) >= 0.5 and abs(q[0]) < 0.5:
        x, y, z, w = q
    else:
        w, x, y, z = q
    return w, x, y, z

def quat_to_rot(q):
    w, x, y, z = quat_to_wxyz(q)
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w),   2*(x*z+y*w)],
        [2*(x*y+z*w),   1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w),   2*(y*z+x*w),   1-2*(x*x+y*y)],
    ], dtype=np.float64)

def get_yaw(q):
    w, x, y, z = quat_to_wxyz(q)
    return math.atan2(2*(w*z + x*y), 1 - 2*(y*y + z*z))

def wrap_pi(a):
    while a > math.pi:  a -= 2*math.pi
    while a < -math.pi: a += 2*math.pi
    return a

def angle_diff(target, current):
    return wrap_pi(target - current)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ─────────────────────────────────────────────
# 10) ToF 레이캐스트(8x8)
# ─────────────────────────────────────────────
def rot_y(angle_rad):
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[ c, 0, s],
                     [ 0, 1, 0],
                     [-s, 0, c]], dtype=np.float64)

SENSOR_MOUNT_PITCH = math.radians(SENSOR_MOUNT_PITCH_DEG)
R_MOUNT = rot_y(SENSOR_MOUNT_PITCH)

TOF_FOV_H = math.radians(TOF_FOV_H_DEG)
TOF_FOV_V = math.radians(TOF_FOV_V_DEG)

az_list = np.linspace(-TOF_FOV_H/2, TOF_FOV_H/2, TOF_COLS)
el_list = np.linspace( TOF_FOV_V/2, -TOF_FOV_V/2, TOF_ROWS)

def raycast(origin, direction, max_dist):
    q = omni.physx.get_physx_scene_query_interface().raycast_closest(
        (float(origin[0]), float(origin[1]), float(origin[2])),
        (float(direction[0]), float(direction[1]), float(direction[2])),
        float(max_dist)
    )
    if q["hit"]:
        return True, float(q["distance"])
    return False, float(max_dist)

def add_tof_noise(dist_m, row, col):
    if dist_m <= 0.2:
        sigma = 0.011
    else:
        sigma = 0.05 * dist_m
    noisy = dist_m + rng.normal(0.0, sigma)
    if (row in (0,7)) and (col in (0,7)):
        noisy *= (1.0 + rng.normal(0.0, 0.04))
    return float(np.clip(noisy, TOF_MIN_M, TOF_MAX_M))

def tof_read_8x8(robot_pos, robot_orient, t_now, cache):
    if cache["dist"] is not None and (t_now - cache["t_last"]) < TOF_DT:
        return cache["dist"], cache["hit"]

    R_robot = quat_to_rot(robot_orient)
    origin = robot_pos + (R_robot @ SENSOR_LOCAL_OFFSET)

    dist = np.full((TOF_ROWS, TOF_COLS), TOF_MAX_M, dtype=np.float64)
    hitm = np.zeros((TOF_ROWS, TOF_COLS), dtype=bool)

    for r, el in enumerate(el_list):
        for c, az in enumerate(az_list):
            ce, se = math.cos(el), math.sin(el)
            ca, sa = math.cos(az), math.sin(az)
            d_s = np.array([ce*ca, ce*sa, se], dtype=np.float64)
            d_s = R_MOUNT @ d_s
            d_w = R_robot @ d_s
            n = np.linalg.norm(d_w)
            if n > 1e-9:
                d_w = d_w / n

            hit, d = raycast(origin, d_w, TOF_MAX_M)
            hitm[r, c] = hit
            dist[r, c] = d
            if ENABLE_NOISE and hit:
                dist[r, c] = add_tof_noise(dist[r, c], r, c)

    if APPLY_ZONE_FLIP:
        dist = dist[::-1, ::-1].copy()
        hitm = hitm[::-1, ::-1].copy()

    cache["t_last"] = t_now
    cache["dist"] = dist
    cache["hit"] = hitm
    return dist, hitm

def region_stats(dist, hitm, rows, cols):
    d = dist[np.ix_(rows, cols)].reshape(-1)
    h = hitm[np.ix_(rows, cols)].reshape(-1)
    total = len(d)
    hit_n = int(np.sum(h))
    hit_ratio = hit_n / total if total > 0 else 0.0
    med = float(np.median(d[h])) if hit_n > 0 else TOF_MAX_M
    return med, hit_n, total, hit_ratio

def cliff_flags(dist, hitm, baseline_floor_m):
    Lm, Lhit, Ltot, Lhr = region_stats(dist, hitm, BOTTOM_ROWS, L_COLS)
    Cm, Chit, Ctot, Chr = region_stats(dist, hitm, BOTTOM_ROWS, C_COLS)
    Rm, Rhit, Rtot, Rhr = region_stats(dist, hitm, BOTTOM_ROWS, R_COLS)

    def is_cliff(med, hit_ratio):
        if hit_ratio < MIN_HIT_RATIO:
            return True
        if baseline_floor_m is not None:
            if med > max(ABS_CLIFF_M, baseline_floor_m * RELATIVE_JUMP):
                return True
        else:
            if med > ABS_CLIFF_M:
                return True
        return False

    return (
        (is_cliff(Lm, Lhr), Lm, Lhit, Ltot),
        (is_cliff(Cm, Chr), Cm, Chit, Ctot),
        (is_cliff(Rm, Rhr), Rm, Rhit, Rtot),
    )


# ─────────────────────────────────────────────
# 11) HUD (EN-only, scroll-safe)
# ─────────────────────────────────────────────
def _label_style(size):
    return {"color": COLOR_TEXT, "font_size": int(size*HUD_SCALE)}

class ToFHud:
    def __init__(self):
        self.window = None
        self.status_label = None
        self.sub_label = None
        self.cell_rects = [[None for _ in range(TOF_COLS)] for _ in range(TOF_ROWS)]
        self.cell_texts = [[None for _ in range(TOF_COLS)] for _ in range(TOF_ROWS)]

        if not HUD_ENABLED:
            return

        cell = int(26 * HUD_SCALE)
        spacing = 2
        pad = int(10 * HUD_SCALE)

        flags = 0
        if HUD_NO_DOCKING:
            flags |= ui.WINDOW_FLAGS_NO_DOCKING

        self.window = ui.Window(
            "ToF HUD",
            width=HUD_START_SIZE[0],
            height=HUD_START_SIZE[1],
            position_x=HUD_START_POS[0],
            position_y=HUD_START_POS[1],
            flags=flags,
        )

        with self.window.frame:
            with ui.VStack(spacing=6, style={"background_color": COLOR_BG, "padding": pad}):
                self.status_label = ui.Label("STATE: - | TIME: 00:00", style=_label_style(16))
                self.sub_label = ui.Label("CLIFF: NONE | L:0 C:0 R:0 (mm)", style=_label_style(12))

                # Scroll-safe grid
                # ✅ 변경점: 배열 인덱스(r)는 그대로 두고, "그리는 순서"만 7→0으로 뒤집어서
                #    낙상 판정 구역(BOTTOM_ROWS=[6,7])이 화면 맨 위쪽 2행에 표시되도록 함.
                with ui.ScrollingFrame(height=int((cell*8 + spacing*7 + 10) * 1.2)):
                    with ui.VStack(spacing=spacing):
                        for r in reversed(range(TOF_ROWS)):
                            with ui.HStack(spacing=spacing):
                                for c in range(TOF_COLS):
                                    with ui.ZStack(width=cell, height=cell):
                                        rect = ui.Rectangle(
                                            width=cell, height=cell,
                                            style={"background_color": COLOR_MISS, "border_color": COLOR_BORDER, "border_width": 1}
                                        )
                                        self.cell_rects[r][c] = rect
                                        txt = ui.Label("", alignment=ui.Alignment.CENTER, style=_label_style(10))
                                        self.cell_texts[r][c] = txt

    def _color_for_mm(self, row_idx, mm_val, hit_ok):
        if not hit_ok:
            return COLOR_MISS

        # Rows 0~5 (화면 하단 6행): only GREEN/YELLOW
        if row_idx <= 5:
            return COLOR_OK if mm_val <= MM_GREEN else COLOR_WARN

        # Rows 6~7 (화면 상단 2행 = 낙상 판정 구역): GREEN/YELLOW/ORANGE/RED
        if mm_val <= MM_GREEN:
            return COLOR_OK
        if mm_val <= MM_YELLOW:
            return COLOR_WARN
        if mm_val <= MM_ORANGE:
            return COLOR_ORANGE
        return COLOR_DANGER

    def update(self, t, state, L, C, R, dist, hitm, log_no=None):
        if self.window is None:
            return

        elapsed = f"{int(t)//60:02d}:{int(t)%60:02d}"
        state_name = STATE_EN.get(state, str(state))

        cl, lm, _, _ = L
        cc, cm, _, _ = C
        cr, rm, _, _ = R

        danger_parts = []
        if cl: danger_parts.append("L")
        if cc: danger_parts.append("C")
        if cr: danger_parts.append("R")
        danger_txt = "NONE" if not danger_parts else ",".join(danger_parts)

        prefix = f"#{log_no:03d} " if isinstance(log_no, int) else ""
        self.status_label.text = f"{prefix}STATE: {state_name} | TIME: {elapsed}"
        self.sub_label.text = f"CLIFF: {danger_txt} | L:{lm*1000:.0f} C:{cm*1000:.0f} R:{rm*1000:.0f} (mm)"

        if dist is None or hitm is None:
            return

        mm = (dist * 1000.0).astype(np.int32)

        danger_cols = set()
        if cl: danger_cols |= set(L_COLS)
        if cc: danger_cols |= set(C_COLS)
        if cr: danger_cols |= set(R_COLS)

        for r in range(TOF_ROWS):
            for c in range(TOF_COLS):
                col = self._color_for_mm(r, int(mm[r, c]), bool(hitm[r, c]))

                # Rows 6~7 (화면 상단 2행)만: 위험 ROI에 RED 강제
                if (r in (6, 7)) and (c in danger_cols):
                    col = COLOR_DANGER

                border = COLOR_CLIFFROW_BORDER if r in (6, 7) else COLOR_BORDER

                self.cell_rects[r][c].style = {
                    "background_color": col,
                    "border_color": border,
                    "border_width": 1,
                }
                self.cell_texts[r][c].text = "----" if not hitm[r, c] else f"{int(mm[r, c])}"


# ─────────────────────────────────────────────
# 12) 콘솔 로그(한글만)
# ─────────────────────────────────────────────
def mmss(seconds: float) -> str:
    total = int(seconds)
    return f"{total//60:02d}:{total%60:02d}"

def log_snapshot(log_no, tag, t, state, cmd, yaw, pos, L, C, R):
    tag_ko = TAG_KO.get(tag, tag)
    state_ko = STATE_KO.get(state, state)
    v, w = cmd[0], cmd[1]
    cl, lm, lhit, ltot = L
    cc, cm, chit, ctot = C
    cr, rm, rhit, rtot = R

    def verdict(flag): return "낙상위험" if flag else "정상"

    print("━"*64)
    print(f"[#{log_no:03d} | {tag_ko}]  경과시간: {mmss(t)}  |  상태: {state_ko}")
    print(f"  속도(v): {v:+.3f} m/s   |  회전속도(w): {w:+.2f} rad/s")
    print(f"  방향(yaw): {math.degrees(yaw):+.1f}°  |  위치: ({float(pos[0]):.2f}, {float(pos[1]):.2f}, {float(pos[2]):.2f})")
    print(f"  좌(L): {lm*1000:6.0f} mm (감지 {lhit}/{ltot}) {verdict(cl)} | "
          f"중앙(C): {cm*1000:6.0f} mm (감지 {chit}/{ctot}) {verdict(cc)} | "
          f"우(R): {rm*1000:6.0f} mm (감지 {rhit}/{rtot}) {verdict(cr)}")
    print("━"*64)


# ─────────────────────────────────────────────
# 13) 상태머신
# ─────────────────────────────────────────────
timer = {"steps": 0}
scan  = {"total_rad": 0.0, "safe_cnt": 0}

YAW_TOL = math.radians(7.0)
BYPASS_ALIGN_TOL = math.radians(12)

def heading_hold(v, yaw, yaw_ref):
    err = angle_diff(yaw_ref, yaw)
    w = clamp(1.8*err, -TURN_RATE, TURN_RATE)
    return [v, w]

def decide(state, L, C, R, pos, orient, yaw_ref_fwd, yaw_ref_left):
    cl,_,_,_ = L
    cc,_,_,_ = C
    cr,_,_,_ = R

    x, y = float(pos[0]), float(pos[1])
    yaw = get_yaw(orient)

    if state == S_FORWARD:
        if x >= EDGE_GUARD_X:
            timer["steps"] = 0
            return S_STOP, [0.0, 0.0]
        if cc or (cl and cr):
            timer["steps"] = 0
            return S_STOP, [0.0, 0.0]
        return S_FORWARD, heading_hold(BASE_SPEED, yaw, yaw_ref_fwd)

    if state == S_STOP:
        timer["steps"] += 1
        if timer["steps"] >= STOP_STEPS:
            timer["steps"] = 0
            return S_REVERSE, [-REVERSE_SPEED, 0.0]
        return S_STOP, [0.0, 0.0]

    if state == S_REVERSE:
        timer["steps"] += 1
        if timer["steps"] >= REVERSE_STEPS:
            scan["total_rad"] = 0.0
            scan["safe_cnt"] = 0
            return S_SCANNING, [0.0, 0.0]
        return S_REVERSE, [-REVERSE_SPEED, 0.0]

    if state == S_SCANNING:
        err_to_left = angle_diff(yaw_ref_left, yaw)
        w = clamp(2.2*err_to_left, -SCAN_RATE, SCAN_RATE)
        scan["total_rad"] += abs(w) * PHYSICS_DT
        scan["safe_cnt"] = scan["safe_cnt"] + 1 if (not cc) else 0

        if scan["safe_cnt"] >= SAFE_NEED:
            return S_TO_BYPASS, [0.0, 0.0]
        if scan["total_rad"] >= MAX_SCAN_RAD:
            return S_DONE, [0.0, 0.0]
        return S_SCANNING, [0.0, w]

    if state == S_TO_BYPASS:
        diff = angle_diff(yaw_ref_left, yaw)
        if abs(diff) > BYPASS_ALIGN_TOL:
            return S_TO_BYPASS, [0.0, TURN_RATE*np.sign(diff)]
        cmd = heading_hold(BASE_SPEED, yaw, yaw_ref_left)
        if y >= BYPASS_Y_TARGET:
            return S_TURN_FWD, [0.0, 0.0]
        return S_TO_BYPASS, cmd

    if state == S_TURN_FWD:
        diff = angle_diff(yaw_ref_fwd, yaw)
        if abs(diff) <= YAW_TOL:
            return S_DESCEND, [0.0, 0.0]
        return S_TURN_FWD, [0.0, TURN_RATE*np.sign(diff)]

    if state == S_DESCEND:
        if float(pos[0]) > BYPASS_RAMP_END:
            return S_DONE, [0.0, 0.0]
        return S_DESCEND, heading_hold(BASE_SPEED, yaw, yaw_ref_fwd)

    return S_DONE, [0.0, 0.0]


# ─────────────────────────────────────────────
# 14) 메인 루프
# ─────────────────────────────────────────────
my_world.reset()

step = 0
reset_needed = False
state = S_FORWARD

printed_init = False
last_periodic_t = -1e9
log_count = 0

tof_cache = {"t_last": -1e9, "dist": None, "hit": None}

yaw_ref_fwd = None
yaw_ref_left = None

hud = ToFHud()

print("━"*64)
print("🦽 Final5 (TOP-CLIFF): 터미널=한글 / HUD=영어(한글 미사용) / 낙상 판정 구역=화면 상단 적용 완료")
print("━"*64)

while simulation_app.is_running():
    my_world.step(render=True)

    if my_world.is_stopped() and not reset_needed:
        reset_needed = True

    if my_world.is_playing():
        if reset_needed:
            my_world.reset(); my_ctrl.reset()
            reset_needed = False
            step = 0
            state = S_FORWARD
            printed_init = False
            last_periodic_t = -1e9
            log_count = 0
            scan["total_rad"] = 0.0
            scan["safe_cnt"] = 0
            tof_cache["t_last"] = -1e9
            tof_cache["dist"] = None
            tof_cache["hit"] = None
            baseline["floor_m"] = None
            yaw_ref_fwd = None
            yaw_ref_left = None

        pos, orient = my_jetbot.get_world_pose()
        yaw = get_yaw(orient)
        t = step * PHYSICS_DT

        if yaw_ref_fwd is None:
            yaw_ref_fwd = yaw
            yaw_ref_left = wrap_pi(yaw + math.pi/2)

        dist, hitm = tof_read_8x8(pos, orient, t, tof_cache)
        L, C, R = cliff_flags(dist, hitm, baseline["floor_m"])

        # baseline 갱신: 중앙(C)이 안전일 때만
        cc, c_m, c_hit, c_tot = C
        if (not cc) and (c_tot > 0) and ((c_hit / c_tot) >= MIN_HIT_RATIO):
            if baseline["floor_m"] is None:
                baseline["floor_m"] = c_m
            else:
                baseline["floor_m"] = (1.0-BASELINE_ALPHA)*baseline["floor_m"] + BASELINE_ALPHA*c_m

        state_next, cmd = decide(state, L, C, R, pos, orient, yaw_ref_fwd, yaw_ref_left)
        my_jetbot.apply_wheel_actions(my_ctrl.forward(command=cmd))

        # HUD 업데이트(영어만)
        hud.update(t, state_next, L, C, R, dist, hitm, log_no=(log_count if log_count > 0 else None))

        # 콘솔 로그(한글)
        if not printed_init:
            log_count += 1
            log_snapshot(log_count, "INIT", t, state_next, cmd, yaw, pos, L, C, R)
            printed_init = True
            last_periodic_t = t
        elif state_next != state:
            log_count += 1
            log_snapshot(log_count, "STATE_CHANGE", t, state_next, cmd, yaw, pos, L, C, R)
            last_periodic_t = t
        elif (t - last_periodic_t) >= LOG_INTERVAL_SEC:
            log_count += 1
            log_snapshot(log_count, "HEARTBEAT", t, state_next, cmd, yaw, pos, L, C, R)
            last_periodic_t = t

        state = state_next
        step += 1

    if args.test and step > 600:
        break

my_world.stop()
simulation_app.close()
