# isaacsim
아이작 심 환경구축

# 🤖 Isaac Sim 5.1.0 Windows 설치 트러블슈팅

> **Isaac Sim이 실행 직후 크래시된다면, 이 문서가 도움이 될 수 있습니다.**  
> 드라이버 버전 비호환으로 인한 GUI 크래시 문제와 해결 방법을 정리했습니다.

<br>

## 📋 목차

1. [이런 분들께 도움이 됩니다](#-이런-분들께-도움이-됩니다)
2. [테스트 환경](#-테스트-환경)
3. [문제 증상](#-문제-증상)
4. [원인](#-원인)
5. [해결 방법](#-해결-방법)
   - [Step 1. 드라이버 버전 확인](#step-1-드라이버-버전-확인)
   - [Step 2. DDU로 드라이버 완전 삭제](#step-2-ddu로-드라이버-완전-삭제)
   - [Step 3. 권장 드라이버 580.88 설치](#step-3-권장-드라이버-58088-설치)
6. [Isaac Sim 5.1.0 설치 방법 (Windows)](#-isaac-sim-510-설치-방법-windows)
7. [정상 동작 확인](#-정상-동작-확인)
8. [주의사항](#-주의사항)
9. [참고 링크](#-참고-링크)

<br>

---

## 🙋 이런 분들께 도움이 됩니다

- Isaac Sim 5.1.0 실행 시 **20초 내외로 크래시**가 발생하는 분
- `rtx.scenedb.plugin.dll` 또는 `omni.kit.window.preferences` **Access Violation** 에러가 뜨는 분
- **Headless 모드는 되는데 GUI 모드만 안 되는** 분
- 드라이버를 **595.x 계열**로 사용 중인 분
- Isaac Sim을 **처음 설치**하는 분

<br>

---

## 💻 테스트 환경

| 항목 | 사양 |
|---|---|
| OS | Windows 11 |
| CPU | AMD Ryzen 9 7945HX |
| RAM | 32GB |
| GPU | NVIDIA GeForce RTX 4070 Laptop GPU (8GB VRAM) |
| Isaac Sim 버전 | 5.1.0 |
| 해결된 드라이버 버전 | **580.88** |

<br>

---

## ❌ 문제 증상

Isaac Sim 5.1.0 실행 후 약 20초 뒤 아무런 경고 없이 종료되거나, 아래와 같은 에러가 발생합니다.

```
Access violation in omni.kit.window.preferences extension,
approximately 20 seconds after application reports ready state.
```

**공통 특징:**
- Isaac Sim 버전을 바꿔도(4.5.0, 5.0.0, 5.1.0) 동일하게 크래시
- `--headless` 옵션으로 실행하면 정상 작동
- 셰이더 캐시 삭제, 재설치 등 일반적인 조치로는 해결 안 됨

<br>

---

## 🔍 원인

**NVIDIA 드라이버 `595.x` 계열의 Vulkan 렌더링 경로 버그**가 원인입니다.

Isaac Sim GUI 모드는 기본적으로 Vulkan 렌더러를 사용하는데, 595.x 드라이버에서 이 경로에 버그가 있어 크래시가 발생합니다. Headless 모드는 D3D12 렌더러를 사용하기 때문에 영향을 받지 않습니다.

> 이 내용은 [NVIDIA 공식 개발자 포럼 (2026.04.01)](https://forums.developer.nvidia.com/t/isaac-sim-5-1-gui-crash-access-violation-on-rtx-5070-ti-blackwell-fixed-by-driver-downgrade-to-591-74/365335) 에서 NVIDIA 직원에 의해 공식 확인된 내용입니다.

### 드라이버 버전별 동작 여부

| 드라이버 버전 | Isaac Sim 5.1.0 GUI 동작 |
|:---:|:---:|
| 595.79 | ❌ 크래시 |
| 591.74 | ✅ 동작 (커뮤니티 확인) |
| **580.88** | ✅ **동작 (NVIDIA 공식 권장)** |

<br>

---

## ✅ 해결 방법

### Step 1. 드라이버 버전 확인

CMD 또는 PowerShell에서 아래 명령어를 실행합니다.

```powershell
nvidia-smi
```

출력 상단에서 `Driver Version`을 확인합니다.

```
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 595.79   Driver Version: 595.79   CUDA Version: 13.2  |
```

**`595.x` 계열이라면 아래 Step 2, 3을 진행하세요.**

<br>

### Step 2. DDU로 드라이버 완전 삭제

일반 제거는 잔여 파일이 남아 충돌을 일으킬 수 있습니다. **DDU(Display Driver Uninstaller)** 를 사용해 완전히 삭제합니다.

> ⚠️ **안전 모드에서 진행하는 것을 강력 권장합니다.**

#### 안전 모드 진입

```
방법 1: Win + R → msconfig → 부팅 탭 → 안전 부팅 체크 → 확인 → 재시작
방법 2: 설정 → 시스템 → 복구 → 고급 시작 → 지금 다시 시작
        → 문제 해결 → 고급 옵션 → 시작 설정 → 다시 시작 → [4] 안전 모드 선택
```

#### DDU 실행

1. [DDU 다운로드 (wagnardsoft.com)](https://www.wagnardsoft.com/DDU)
2. 안전 모드 진입 후 DDU 실행
3. 왼쪽 상단 드롭다운에서 `GPU` 선택
4. 오른쪽 드롭다운에서 `NVIDIA` 선택
5. **"Clean and restart"** 클릭

<br>

### Step 3. 권장 드라이버 580.88 설치

👉 **[NVIDIA 드라이버 580.88 다운로드 (공식)](https://www.nvidia.com/download/driverResults.aspx/251256/en-us/)**

#### 설치 시 주의사항

1. **라이선스 동의 화면**: `NVIDIA 그래픽 드라이버` 선택 (NVIDIA App 제외 권장)
   - NVIDIA App은 드라이버를 자동 업데이트해서 다시 595.x로 올릴 수 있습니다
2. **설치 옵션**: `사용자 정의 설치 (고급)` 선택
3. `전체 설치 수행 (Perform a clean installation)` **체크 확인**
4. 설치 완료 후 재시작

#### 설치 확인

```powershell
nvidia-smi
# Driver Version: 580.88 이 출력되면 완료
```

<br>

---

## 📦 Isaac Sim 5.1.0 설치 방법 (Windows)

드라이버 교체 후 아래 순서로 Isaac Sim을 설치합니다.

### 1. 다운로드

👉 [Isaac Sim 5.1.0 다운로드 페이지](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/download.html)

`Windows x86_64` 버전 zip 파일을 다운로드합니다.

### 2. 설치 폴더 생성 및 압축 해제

```powershell
mkdir C:\isaacsim
tar -xvzf "$env:USERPROFILE\Downloads\isaac-sim-standalone-5.1.0-windows-x86_64.zip" -C C:\isaacsim
```

### 3. post_install 실행

```powershell
cd C:\isaacsim
.\post_install.bat
```

아래 메시지가 출력되면 정상입니다.

```
Symlink extension_examples created.
```

### 4. Isaac Sim 실행

```powershell
.\isaac-sim.selector.bat
```

App Selector 창이 열리면:
- **Isaac-sim** 선택 (기본값)
- **START** 클릭

> ⏳ **최초 실행 시 셰이더 컴파일로 5~15분 소요됩니다.** 화면이 멈춘 것처럼 보여도 기다려 주세요.

<br>

---

## 🟢 정상 동작 확인

Isaac Sim 실행 후 아래 방법으로 정상 동작을 확인합니다.

```
상단 메뉴 → Create → Environment → Simple Room
```

씬이 정상적으로 로드되면 설치 완료입니다.

<br>

---

## ⚠️ 주의사항

### 드라이버 자동 업데이트 방지
NVIDIA App 또는 GeForce Experience가 설치되어 있으면 드라이버를 자동으로 최신 버전으로 업데이트할 수 있습니다. Isaac Sim 사용 중에는 **자동 업데이트를 비활성화**하거나, 드라이버 설치 시 NVIDIA App을 함께 설치하지 않는 것을 권장합니다.

### RTX 4070 Laptop GPU (8GB VRAM) 사용자
공식 최소 사양은 16GB VRAM이지만, 기본적인 씬은 동작합니다. 다만 복잡한 씬이나 다수의 센서를 사용하는 경우 VRAM 부족 문제가 발생할 수 있습니다.

### Isaac Sim 5.1.0 공식 시스템 요구사항

| 항목 | 최소 | 권장 |
|---|---|---|
| GPU | GeForce RTX 4080 | GeForce RTX 5080 |
| VRAM | 16GB | 16GB+ |
| RAM | 32GB | 64GB |
| Storage | 50GB SSD | 500GB NVMe SSD |
| Driver (Windows) | **580.88** | 580.88 |
| OS | Windows 10/11 | Windows 11 |

<br>

---

## 🔗 참고 링크

| 자료 | 링크 |
|---|---|
| Isaac Sim 5.1.0 공식 문서 | [docs.isaacsim.omniverse.nvidia.com](https://docs.isaacsim.omniverse.nvidia.com/5.1.0) |
| Isaac Sim 시스템 요구사항 | [requirements.html](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html) |
| Isaac Sim 다운로드 | [download.html](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/download.html) |
| Isaac Sim Quick Install | [quick-install.html](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/quick-install.html) |
| NVIDIA 드라이버 580.88 | [공식 다운로드](https://www.nvidia.com/download/driverResults.aspx/251256/en-us/) |
| DDU 다운로드 | [wagnardsoft.com](https://www.wagnardsoft.com/DDU) |
| NVIDIA 포럼 (595.79 버그 리포트) | [포럼 링크](https://forums.developer.nvidia.com/t/isaac-sim-5-1-gui-crash-access-violation-on-rtx-5070-ti-blackwell-fixed-by-driver-downgrade-to-591-74/365335) |

<br>

---

> 이 문서가 도움이 되셨다면 ⭐ Star를 눌러주세요!  
> 추가적인 문제나 다른 GPU 환경에서의 경험은 Issue 또는 PR로 공유해 주시면 감사합니다. 🙏
