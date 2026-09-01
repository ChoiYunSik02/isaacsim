# Wheelchair Cliff (Fall) Detection — Isaac Sim

VL53L8CX 8×8 ToF 센서를 이용해 전동 휠체어의 낙상(계단, 턱 등 절벽 지형) 위험을 감지하고 우회 경로를 안내하는 시뮬레이션입니다. NVIDIA Isaac Sim 5.1.0에서 동작합니다.

## Files

- `wheelchair_cliff_sim_final5_top.py` — 8×8 ToF depth map 기반 낙상 감지 + 우회 네비게이션 시뮬레이션 (Final5, HUD 상단 정렬 버전)
  - 상단 2행(Row 6~7)은 낙상 판정 구역(초록/노랑/주황/빨강), 하단 6행(Row 0~5)은 원거리 모니터링(초록/노랑만)으로 색상 규칙을 분리
  - 콘솔 로그는 한글, HUD 창은 인코딩 깨짐 방지를 위해 영문만 사용
- `wheelchair_tof_analysis.pptx` — ToF 센서 데이터 분석 발표자료
- `demo.mp4` — Isaac Sim 낙상감지 시뮬레이션 실행 영상

## Run

```powershell
C:\isaacsim\python.bat wheelchair_cliff_sim_final5_top.py
```

Isaac Sim 설치 및 ToF 센서 시뮬레이션 파이프라인 전체 흐름은 저장소 루트의 `project.md`를 참고하세요.
