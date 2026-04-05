# 🦽 Isaac Sim 5.1.0 — ToF 센서 데이터 수집 전체 가이드

> 휠체어 자율주행을 위한 ToF 센서 시뮬레이션 데이터 수집 파이프라인  
> Isaac Sim 5.1.0 / Windows 11 / RTX 4070 Laptop 기준

---

## 📋 전체 흐름

```
Step 1. 실내 씬 만들기
Step 2. 휠체어(모바일 로봇) 배치
Step 3. ToF 센서 부착
Step 4. Replicator로 장애물 랜덤 배치 자동화
Step 5. ToF 데이터 자동 수집 (8x8 depth map)
Step 6. XGBoost 모델 학습
Step 7. 실제 휠체어에 모델 탑재
```

---

## Step 1. 실내 씬 만들기

### 1-1. Isaac Sim 실행

```powershell
cd C:\isaacsim
.\isaac-sim.selector.bat
```

App Selector에서 **Isaac-sim** 선택 → **START**

---

### 1-2. 기본 씬 불러오기

Isaac Sim이 완전히 로드되면:

```
상단 메뉴 → File → New
```

빈 씬에서 시작합니다.

---

### 1-3. 복도/실내 환경 만들기

Isaac Sim에 내장된 환경을 사용하는 방법과 직접 만드는 방법이 있습니다.

#### 방법 A. 내장 환경 사용 (빠름, 권장)

```
상단 메뉴 → Create → Environment → Simple Room
```

Simple Room이 로드되면 기본 실내 환경이 생성됩니다.

복도처럼 좁고 긴 느낌을 원한다면:

```
Stage 패널(우측) → Environment → Room 선택
→ 속성 패널에서 Scale X 줄이고 Scale Z 늘리기
  예) Scale: X=0.5, Y=1.0, Z=2.0
```

#### 방법 B. 직접 바닥 + 벽 만들기 (커스텀)

```
Create → Mesh → Plane  → 바닥으로 사용
Create → Mesh → Cube   → 벽으로 사용 (Scale로 얇게 만들기)
```

벽 4개를 배치해서 복도 형태를 만듭니다.

| 오브젝트 | Scale (X, Y, Z) | Position |
|---|---|---|
| 바닥 (Plane) | 10, 1, 5 | 0, 0, 0 |
| 앞벽 (Cube) | 10, 0.1, 3 | 0, 2.5, 1.5 |
| 뒷벽 (Cube) | 10, 0.1, 3 | 0, -2.5, 1.5 |
| 좌벽 (Cube) | 0.1, 5, 3 | -5, 0, 1.5 |
| 우벽 (Cube) | 0.1, 5, 3 | 5, 0, 1.5 |

> 단위: 미터(m)

---

### 1-4. 조명 추가

```
Create → Light → Sphere Light (또는 Distant Light)
```

씬이 너무 어두우면 조명 Intensity를 높여줍니다.

```
조명 선택 → 우측 속성 패널 → Intensity: 5000 정도로 설정
```

---

### 1-5. 씬 저장

```
File → Save As → C:\isaacsim_projects\wheelchair_scene.usd
```

---

## Step 2. 휠체어(모바일 로봇) 배치

Isaac Sim에는 기본 제공 모바일 로봇이 있습니다. 실제 휠체어 모델 대신 이걸로 먼저 테스트합니다.

---

### 2-1. 기본 제공 로봇 불러오기

```
상단 메뉴 → Create → Robots → Nova Carter
```

또는

```
Create → Robots → Jetbot  (더 가볍고 단순, 테스트용 권장)
```

로봇이 씬에 배치되면 Stage 패널에 `/World/Jetbot` 항목이 생성됩니다.

---

### 2-2. 로봇 위치 설정

로봇을 복도 입구 쪽에 배치합니다.

```
Stage 패널 → Jetbot 선택
→ 우측 속성 패널 → Transform
  Position: X=0, Y=-3, Z=0.1  (바닥 위에 올려놓기)
  Rotation: X=0, Y=0, Z=0
```

---

### 2-3. Physics 설정 확인

로봇이 물리 시뮬레이션을 받도록 설정합니다.

```
상단 메뉴 → Play 버튼(▶) 눌러서 시뮬레이션 시작
→ 로봇이 바닥에 안착하면 정상
→ Stop(■) 버튼으로 정지
```

> ⚠️ Play 상태에서는 씬을 편집할 수 없으니 항상 Stop 후 편집하세요.

---

## Step 3. ToF 센서 부착

ToF 센서는 Isaac Sim의 **Depth Camera**로 시뮬레이션합니다.  
실제 ToF 센서(8x8 해상도)와 동일하게 해상도를 낮춰서 사용합니다.

---

### 3-1. 카메라 센서 추가

```
Stage 패널 → Jetbot 선택 (로봇 하위에 추가할 것)
→ 우클릭 → Create → Camera
```

Stage 패널에 `/World/Jetbot/Camera` 가 생성됩니다.

---

### 3-2. 카메라 위치 설정 (센서 위치 조정)

```
Stage 패널 → Camera 선택
→ 속성 패널 → Transform
  Position: X=0, Y=0.3, Z=0.5   (로봇 앞쪽 중앙, 높이 0.5m)
  Rotation: X=0, Y=0, Z=0       (정면을 향하도록)
```

---

### 3-3. 카메라 해상도 및 속성 설정

ToF 센서 8x8 해상도를 맞춥니다.

```
Camera 선택 → 속성 패널
  Horizontal Aperture: 맞게 조절
  Focal Length: 1.93  (ToF 센서 화각에 맞게)
  Clipping Range: Near=0.1, Far=4.0  (최대 측정 거리 4m)
```

---

### 3-4. Render Product 설정 (depth 데이터 추출용)

Python 스크립트에서 depth map을 추출하기 위한 설정입니다.  
이 부분은 Step 5의 스크립트에서 자동으로 처리됩니다.

---

## Step 4. Replicator로 장애물 랜덤 배치

Isaac Sim의 **Replicator**를 사용해서 사람/장애물을 0~4m 거리에 자동으로 랜덤 배치합니다.

---

### 4-1. 장애물 오브젝트 준비

테스트용 간단한 장애물(사람 모양 대신 박스)을 먼저 사용합니다.

```
Create → Mesh → Capsule  (사람 형태 근사)
→ Scale: X=0.4, Y=0.4, Z=1.7  (성인 체형)
→ 이름: "Obstacle_Person"
```

나중에 실제 사람 에셋으로 교체 가능합니다:
```
Window → Simulation → People (Isaac Sim People 확장)
```

---

### 4-2. Replicator 스크립트 작성

아래 Python 스크립트를 `C:\isaacsim_projects\replicator_setup.py` 로 저장합니다.

```python
import omni.replicator.core as rep

with rep.new_layer():
    
    # 씬 카메라 (ToF 센서) 참조
    camera = rep.get.prim_at_path("/World/Jetbot/Camera")
    
    # 장애물 오브젝트 참조
    obstacle = rep.get.prim_at_path("/World/Obstacle_Person")
    
    # 랜덤 배치 설정
    with rep.trigger.on_frame(num_frames=1000):  # 1000프레임 수집
        with obstacle:
            rep.modify.pose(
                position=rep.distribution.uniform(
                    (-1.0, 0.3, 0.0),   # X: 좌우 ±1m, Y: 앞 0.3m~, Z: 바닥
                    (1.0, 4.0, 0.0)     # X: 좌우 ±1m, Y: 앞 최대 4m, Z: 바닥
                ),
                rotation=rep.distribution.uniform(
                    (0, 0, -180),
                    (0, 0, 180)
                )
            )
```

---

### 4-3. Replicator 스크립트 실행

Isaac Sim 상단 메뉴:

```
Window → Script Editor
→ 위 스크립트 붙여넣기
→ Run 버튼 클릭
```

---

## Step 5. ToF 데이터 자동 수집 (8x8 depth map)

장애물이 랜덤 배치될 때마다 depth map을 캡처하고 8x8로 다운샘플링합니다.

---

### 5-1. 데이터 수집 스크립트

`C:\isaacsim_projects\collect_tof_data.py` 로 저장합니다.

```python
import omni.replicator.core as rep
import numpy as np
import csv
import os
from PIL import Image

# 저장 경로
SAVE_DIR = "C:/isaacsim_projects/tof_data"
os.makedirs(SAVE_DIR, exist_ok=True)

# Render Product 생성 (depth 카메라)
render_product = rep.create.render_product(
    "/World/Jetbot/Camera",
    resolution=(8, 8)  # 직접 8x8로 렌더링
)

# Annotator 설정 (depth 데이터 추출)
depth_annotator = rep.AnnotatorRegistry.get_annotator("distance_to_camera")
depth_annotator.attach([render_product])

# CSV 파일 준비
csv_path = os.path.join(SAVE_DIR, "tof_dataset.csv")

# 헤더: zone_0_0 ~ zone_7_7 (64개) + label
header = [f"zone_{r}_{c}" for r in range(8) for c in range(8)] + ["label"]

with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)

def get_label(depth_map):
    """
    평균 거리를 기반으로 라벨 분류
    - label 0: 정지 (0~0.5m)
    - label 1: 경고 (0.5~2.0m)
    - label 2: 정상 (2.0m 이상 또는 감지 없음)
    """
    min_dist = np.min(depth_map[depth_map < 4000])  # 4000mm 미만만
    if min_dist < 500:
        return 0  # Stop
    elif min_dist < 2000:
        return 1  # Warning
    else:
        return 2  # Normal

def collect_frame():
    """한 프레임의 ToF 데이터를 수집하여 CSV에 저장"""
    depth_data = depth_annotator.get_data()
    
    if depth_data is None:
        return
    
    # mm 단위 변환 (Isaac Sim은 기본 m 단위)
    depth_mm = depth_data * 1000.0
    
    # 8x8 배열로 reshape
    depth_8x8 = depth_mm.reshape(8, 8)
    
    # status 필터링: 4000mm 초과는 4000으로 클리핑
    depth_8x8 = np.clip(depth_8x8, 0, 4000)
    
    # 라벨 계산
    label = get_label(depth_8x8)
    
    # CSV 저장
    row = depth_8x8.flatten().tolist() + [label]
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

# Replicator와 연동하여 매 프레임 수집
with rep.new_layer():
    with rep.trigger.on_frame(num_frames=1000):
        rep.utils.send_og_event(event_name="collect_frame")

# 실행
rep.orchestrator.run()
print(f"데이터 수집 완료: {csv_path}")
```

---

### 5-2. 수집 데이터 확인

```python
import pandas as pd

df = pd.read_csv("C:/isaacsim_projects/tof_data/tof_dataset.csv")
print(df.shape)          # 행 수, 열 수 확인
print(df["label"].value_counts())  # 라벨 분포 확인
print(df.head())
```

---

### 5-3. 라벨 정의 정리

| 라벨 | 의미 | 거리 기준 |
|:---:|---|---|
| 0 | 🔴 정지 (Stop) | 최소 거리 0 ~ 500mm |
| 1 | 🟡 경고 (Warning) | 최소 거리 500 ~ 2000mm |
| 2 | 🟢 정상 (Normal) | 최소 거리 2000mm 이상 |

> 실제 프로젝트 요구에 맞게 거리 기준을 조정하세요.

---

## Step 6. XGBoost 모델 학습

수집한 CSV 데이터로 XGBoost 분류 모델을 학습합니다.

---

### 6-1. 필요 패키지 설치

```bash
pip install xgboost scikit-learn pandas numpy matplotlib joblib
```

---

### 6-2. 학습 스크립트

`C:\isaacsim_projects\train_xgboost.py` 로 저장합니다.

```python
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import joblib
import os

# ── 1. 데이터 로드 ──────────────────────────────────────────
df = pd.read_csv("C:/isaacsim_projects/tof_data/tof_dataset.csv")

X = df.drop(columns=["label"]).values   # 64개 zone 값
y = df["label"].values                   # 0, 1, 2

print(f"데이터 수: {len(df)}")
print(f"라벨 분포:\n{pd.Series(y).value_counts()}")

# ── 2. 데이터 분할 ──────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── 3. Data Importance 적용 (가까운 거리에 더 큰 가중치) ────
# 함수: weight = exp((4000 - distance) / 850) - 1
def compute_sample_weight(X):
    min_dist = X.min(axis=1)  # 각 샘플의 최소 거리값
    weight = np.exp((4000 - min_dist) / 850) - 1
    weight = np.clip(weight, 1.0, 50.0)  # 최대 50배 가중치
    return weight

sample_weights = compute_sample_weight(X_train)

# ── 4. 모델 학습 ────────────────────────────────────────────
model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    use_label_encoder=False,
    eval_metric="mlogloss",
    random_state=42
)

model.fit(
    X_train, y_train,
    sample_weight=sample_weights,
    eval_set=[(X_test, y_test)],
    verbose=50
)

# ── 5. 평가 ─────────────────────────────────────────────────
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

print(f"\n✅ Accuracy: {acc * 100:.2f}%")
print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred,
      target_names=["Stop(0)", "Warning(1)", "Normal(2)"]))

# Confusion Matrix 시각화
cm = confusion_matrix(y_test, y_pred)
fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(cm, cmap="Blues")
ax.set_xticks([0,1,2]); ax.set_yticks([0,1,2])
ax.set_xticklabels(["Stop","Warning","Normal"])
ax.set_yticklabels(["Stop","Warning","Normal"])
ax.set_xlabel("Predicted"); ax.set_ylabel("True")
ax.set_title(f"Confusion Matrix (Acc: {acc*100:.2f}%)")
for i in range(3):
    for j in range(3):
        ax.text(j, i, cm[i,j], ha="center", va="center", color="black")
plt.tight_layout()
plt.savefig("C:/isaacsim_projects/confusion_matrix.png")
plt.show()

# ── 6. 모델 저장 ─────────────────────────────────────────────
os.makedirs("C:/isaacsim_projects/model", exist_ok=True)
joblib.dump(model, "C:/isaacsim_projects/model/xgboost_tof.pkl")
print("\n💾 모델 저장 완료: C:/isaacsim_projects/model/xgboost_tof.pkl")
```

---

### 6-3. 학습 실행

```bash
cd C:\isaacsim_projects
python train_xgboost.py
```

---

### 6-4. 예상 결과

참고 논문(단국대 결과 보고서) 기준 XGBoost 성능:

| 지표 | 값 |
|---|---|
| Accuracy | 97.56% |
| FPS (추론 속도) | 207,525 FPS |

실시간 처리에 충분한 속도입니다.

---

## Step 7. 실제 휠체어에 모델 탑재

---

### 7-1. 구성 환경

```
[ToF 센서] ──USB/I2C──▶ [Raspberry Pi 4]
                              │
                         Python 추론 코드
                         (XGBoost 모델)
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
             🔴 Stop 신호          🟢 Go 신호
           (모터 정지 명령)      (모터 구동 유지)
```

---

### 7-2. Raspberry Pi 환경 설정

```bash
pip install xgboost numpy joblib
```

ToF 센서 라이브러리 (VL53L5CX 기준):
```bash
pip install vl53l5cx-python
```

---

### 7-3. 실시간 추론 코드

`wheelchair_inference.py` 로 저장합니다.

```python
import numpy as np
import joblib
import time

# 모델 로드
model = joblib.load("xgboost_tof.pkl")

LABEL_MAP = {
    0: "🔴 STOP    — 장애물 근접! 정지",
    1: "🟡 WARNING — 장애물 감지, 감속",
    2: "🟢 NORMAL  — 정상 주행"
}

def read_tof_sensor():
    """
    실제 ToF 센서(VL53L5CX)에서 8x8 depth 데이터 읽기
    반환값: shape (64,) numpy array, 단위 mm
    """
    # TODO: 실제 센서 라이브러리로 교체
    # 예시: sensor.get_ranging_data() 등
    dummy_data = np.random.uniform(500, 4000, 64)
    return dummy_data

def preprocess(raw_data):
    """
    status 필터링 및 4000mm 클리핑
    """
    processed = np.clip(raw_data, 0, 4000)
    return processed.reshape(1, -1)

def main():
    print("휠체어 ToF 장애물 감지 시작...")
    
    while True:
        # 1. 센서 데이터 읽기
        raw = read_tof_sensor()
        
        # 2. 전처리
        X = preprocess(raw)
        
        # 3. 추론
        label = model.predict(X)[0]
        
        # 4. 결과 출력 및 모터 제어
        print(f"[{time.strftime('%H:%M:%S')}] {LABEL_MAP[label]}")
        
        # TODO: 라벨에 따른 모터 제어 코드 추가
        # if label == 0:
        #     motor.stop()
        # elif label == 1:
        #     motor.slow_down()
        # else:
        #     motor.normal_speed()
        
        time.sleep(0.05)  # 20Hz

if __name__ == "__main__":
    main()
```

---

### 7-4. 실행

```bash
python wheelchair_inference.py
```

---

## 📁 최종 파일 구조

```
C:\isaacsim_projects\
├── wheelchair_scene.usd       # Isaac Sim 씬 파일
├── replicator_setup.py        # Replicator 랜덤 배치 스크립트
├── collect_tof_data.py        # 데이터 수집 스크립트
├── train_xgboost.py           # XGBoost 학습 스크립트
├── confusion_matrix.png       # 평가 결과 이미지
├── tof_data/
│   └── tof_dataset.csv        # 수집된 ToF 데이터
└── model/
    └── xgboost_tof.pkl        # 학습된 모델
```

---

## ⚠️ 주의사항 및 팁

### Isaac Sim 단위계
- Isaac Sim의 기본 단위는 **미터(m)** 입니다.
- ToF 센서 데이터는 **밀리미터(mm)** 단위이므로 `× 1000` 변환 필요합니다.

### 좌표계 차이
- Isaac Sim (센서): **광학 좌표계** (Z-forward)
- ROS: **ROS 좌표계** (X-forward)
- 나중에 ROS 연동 시 좌표 변환 필요합니다.

### 데이터 불균형
Stop 라벨(0~500mm)은 실제로 발생 빈도가 낮아 데이터가 부족할 수 있습니다.  
부족한 라벨은 **Data Augmentation** (Flip, Rotation)을 적용하세요.

```python
# 간단한 Augmentation 예시
def augment(X, y, target_label, target_count):
    mask = y == target_label
    X_target = X[mask]
    y_target = y[mask]
    
    while len(X_target) < target_count:
        # 좌우 반전
        flipped = X_target.reshape(-1, 8, 8)[:, :, ::-1].reshape(-1, 64)
        X_target = np.vstack([X_target, flipped])
        y_target = np.hstack([y_target, np.full(len(flipped), target_label)])
    
    return X_target[:target_count], y_target[:target_count]
```

---

## 🔗 참고 링크

| 자료 | 링크 |
|---|---|
| Isaac Sim Replicator 공식 문서 | https://docs.isaacsim.omniverse.nvidia.com/5.1.0/replicator_tutorials/index.html |
| Isaac Sim Python API | https://docs.isaacsim.omniverse.nvidia.com/5.1.0/reference_python_api.html |
| XGBoost 공식 문서 | https://xgboost.readthedocs.io |
| VL53L5CX 센서 라이브러리 | https://github.com/pimoroni/vl53l5cx-python |
