# Android 센서 데이터 수집 앱 개발 계획서
## Digital Twin 데이터 파이프라인용 고주파 멀티센서 수집 시스템

**작성일**: 2025-11-11
**총 Phase 수**: 300
**예상 개발 기간**: 12-18개월
**목표 플랫폼**: Android 10+ (API 29+), 최적화 Android 14+ (API 34+)

---

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [사용 센서 목록](#사용-센서-목록)
3. [아키텍처 개요](#아키텍처-개요)
4. [개발 Phase 상세](#개발-phase-상세)
5. [품질 보증 체크리스트](#품질-보증-체크리스트)
6. [위험 요소 및 대응 전략](#위험-요소-및-대응-전략)

---

## 프로젝트 개요

### 목적
스마트폰의 다양한 센서(가속도계, 자이로스코프, 마이크, 온도, GPS, 카메라 등)를 고주파 샘플링하여 Raw 데이터로 세션 단위 저장 → 웹으로 안정적 전송 → 데이터레이크 적재 → 디지털 트윈 분석 파이프라인 투입.

### 핵심 요구사항
- ✅ 정확한 타임스탬프 동기화 (UTC + Monotonic)
- ✅ 손실 없는 버퍼링 및 파일화
- ✅ 신뢰성 높은 업로드 (재시도/청크/검증)
- ✅ 경량 센서 융합 (회전벡터 → Euler/Quaternion)
- ✅ 실시간 UI (Jetpack Compose)
- ✅ 포괄적 에러 로깅 및 진단 시스템

---

## 사용 센서 목록

### 1. 모션 센서 (Motion Sensors)
| 센서 타입 | Android Type | 샘플링율 | 용도 |
|---------|--------------|---------|------|
| 가속도계 | TYPE_ACCELEROMETER | 200-400 Hz | 선형 가속도 측정 |
| 자이로스코프 | TYPE_GYROSCOPE | 200-400 Hz | 각속도 측정 |
| 중력 센서 | TYPE_GRAVITY | 100 Hz | 중력 벡터 |
| 선형 가속도 | TYPE_LINEAR_ACCELERATION | 200 Hz | 중력 제외 가속도 |
| 회전 벡터 | TYPE_ROTATION_VECTOR | 100 Hz | 센서 융합 회전 |
| 게임 회전 벡터 | TYPE_GAME_ROTATION_VECTOR | 100 Hz | 자기장 제외 회전 |
| 지자기 회전 벡터 | TYPE_GEOMAGNETIC_ROTATION_VECTOR | 50 Hz | 가속도+자기장 회전 |
| 보행 감지 | TYPE_STEP_DETECTOR | Event | 걸음 감지 |
| 보행 계수 | TYPE_STEP_COUNTER | Event | 누적 걸음 수 |
| 낙하 감지 | TYPE_SIGNIFICANT_MOTION | Event | 큰 움직임 감지 |

### 2. 위치 센서 (Position Sensors)
| 센서 타입 | Android Type | 샘플링율 | 용도 |
|---------|--------------|---------|------|
| 자기장 센서 | TYPE_MAGNETIC_FIELD | 50 Hz | 지자기 벡터 |
| 방위각 센서 | TYPE_ORIENTATION (deprecated) | 50 Hz | 방위 측정 |
| 근접 센서 | TYPE_PROXIMITY | Event | 물체 근접 감지 |

### 3. 환경 센서 (Environmental Sensors)
| 센서 타입 | Android Type | 샘플링율 | 용도 |
|---------|--------------|---------|------|
| 주변 온도 | TYPE_AMBIENT_TEMPERATURE | 1 Hz | 외부 온도 |
| 기압계 | TYPE_PRESSURE | 10 Hz | 대기압 측정 |
| 조도 센서 | TYPE_LIGHT | 5 Hz | 조명 강도 |
| 상대 습도 | TYPE_RELATIVE_HUMIDITY | 1 Hz | 습도 측정 |

### 4. 오디오 센서
| 센서 타입 | API | 샘플링율 | 용도 |
|---------|-----|---------|------|
| 마이크 | AudioRecord | 48 kHz | PCM 오디오 |
| 음압 레벨 | Custom | Real-time | dB 계산 |

### 5. 시스템 센서
| 센서 타입 | API | 샘플링율 | 용도 |
|---------|-----|---------|------|
| GPS | LocationManager | 1-10 Hz | 위치 정보 |
| 배터리 | BatteryManager | 1 Hz | 배터리 상태 |
| 열 상태 | PowerManager | 1 Hz | 열 관리 |
| CPU 사용률 | /proc/stat | 1 Hz | 성능 모니터링 |
| 메모리 | ActivityManager | 1 Hz | 메모리 사용량 |
| 네트워크 | ConnectivityManager | Event | 연결 상태 |

### 6. 카메라/이미지 센서
| 센서 타입 | API | 샘플링율 | 용도 |
|---------|-----|---------|------|
| 카메라 메타데이터 | Camera2 | Event | 노출/ISO/초점 |
| 이미지 스냅샷 | CameraX | 0.1-1 Hz | 주기적 캡처 |

### 7. 생체 센서 (있는 경우)
| 센서 타입 | Android Type | 샘플링율 | 용도 |
|---------|--------------|---------|------|
| 심박수 | TYPE_HEART_RATE | 1 Hz | 심박 측정 |
| 심박 변이도 | TYPE_HEART_BEAT | Event | PPG 신호 |

---

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                       UI Layer (Compose)                     │
│  LiveScreen │ SessionsScreen │ UploadsScreen │ Settings     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    Domain Layer (Use Cases)                  │
│  StartSession │ StopSession │ EnqueueUpload │ ErrorReporting│
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                      Data Layer                              │
├─────────────────┬──────────────┬──────────────┬─────────────┤
│  Sensor Sources │ Buffer Layer │ Upload Queue │ Error Logger│
│  (15+ sensors)  │ (Protobuf+   │ (HTTP/WS)    │ (Structured)│
│                 │  Zstd)       │              │             │
└─────────────────┴──────────────┴──────────────┴─────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│               Services & Workers                             │
│  ForegroundService │ WorkManager │ BackgroundSync           │
└─────────────────────────────────────────────────────────────┘
```

### 모듈 구조
```
app/
├── data/
│   ├── sensor/          # 15+ 센서 소스
│   ├── buffer/          # 청크 라이터
│   ├── upload/          # 업로드 시스템
│   ├── storage/         # 파일 관리
│   └── error/           # 에러 로깅
├── domain/
│   ├── models/          # 데이터 모델
│   ├── usecase/         # 비즈니스 로직
│   └── repository/      # 추상화 계층
├── ui/
│   ├── live/            # 실시간 모니터링
│   ├── sessions/        # 세션 관리
│   ├── uploads/         # 업로드 상태
│   ├── settings/        # 설정
│   └── diagnostics/     # 진단/에러 뷰
├── service/
│   └── RecorderForegroundService.kt
├── worker/
│   └── UploadWorker.kt
└── util/
    ├── TimeSync.kt
    ├── Compression.kt
    └── ErrorTracker.kt
```

---

## 개발 Phase 상세

### 🏗️ **Phase 1-20: 프로젝트 설정 및 기초 인프라**

#### Phase 1: 프로젝트 생성 및 초기화
- [ ] Android Studio 프로젝트 생성 (Kotlin, minSdk 29, targetSdk 34)
- [ ] Git 저장소 초기화 및 .gitignore 설정
- [ ] 프로젝트 디렉토리 구조 생성

#### Phase 2: Gradle 설정 및 의존성 관리
- [ ] Kotlin DSL (build.gradle.kts) 설정
- [ ] 버전 카탈로그 (libs.versions.toml) 생성
- [ ] 기본 라이브러리 의존성 추가:
  - Jetpack Compose BOM
  - Kotlin Coroutines
  - Hilt
  - AndroidX Core/Lifecycle

#### Phase 3: Hilt 의존성 주입 설정
- [ ] Hilt Application 클래스 생성
- [ ] @HiltAndroidApp 어노테이션 적용
- [ ] Application 태그 AndroidManifest.xml 등록
- [ ] Hilt Gradle 플러그인 설정

#### Phase 4: 기본 권한 선언
- [ ] AndroidManifest.xml 권한 추가:
  - INTERNET, ACCESS_NETWORK_STATE
  - RECORD_AUDIO
  - ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION
  - CAMERA
  - FOREGROUND_SERVICE, FOREGROUND_SERVICE_MICROPHONE
  - FOREGROUND_SERVICE_DATA_SYNC
  - POST_NOTIFICATIONS (Android 13+)
  - WAKE_LOCK

#### Phase 5: 런타임 권한 요청 시스템
- [ ] PermissionManager 유틸리티 클래스 생성
- [ ] Accompanist Permissions 라이브러리 통합
- [ ] 권한 요청 Composable 작성
- [ ] 권한 상태 ViewModel 생성

#### Phase 6: 타임스탬프 동기화 시스템
- [ ] TimeSync.kt 생성
- [ ] t0_utc_epoch_ms (Instant.now().toEpochMilli())
- [ ] t0_elapsed_ns (SystemClock.elapsedRealtimeNanos())
- [ ] UTC ↔ Elapsed 변환 함수
- [ ] 타임스탬프 검증 로직

#### Phase 7: 데이터 모델 기초 클래스
- [ ] ChunkHeader.kt (deviceId, sessionId, stream, seq, codec, sha256)
- [ ] Manifest.kt (센서 목록, 샘플링율, 기기 정보)
- [ ] SessionMetadata.kt (시작/종료 시간, 파일 수, 용량)
- [ ] DeviceInfo.kt (Build.MODEL, SDK, Manufacturer)

#### Phase 8: Protobuf 스키마 정의
- [ ] protobuf-lite 의존성 추가
- [ ] acc_sample.proto (AccSample, AccChunk)
- [ ] gyro_sample.proto
- [ ] rotation_sample.proto
- [ ] mag_sample.proto
- [ ] pressure_sample.proto
- [ ] audio_meta.proto
- [ ] Gradle protobuf 플러그인 설정

#### Phase 9: 압축 유틸리티 (Zstd)
- [ ] Compression.kt 인터페이스 정의
- [ ] ZstdCompressor 구현 (zstd-jni 라이브러리)
- [ ] GzipCompressor fallback 구현
- [ ] 압축 레벨 설정 (기본: 3, 최대: 9)
- [ ] 압축/해제 단위 테스트

#### Phase 10: SHA-256 해싱 유틸리티
- [ ] Hasher.kt 생성
- [ ] ByteArray.sha256() 확장 함수
- [ ] File.sha256() 확장 함수
- [ ] InputStream 청크 해싱 (메모리 효율)
- [ ] 해시 검증 로직

#### Phase 11: 파일 네이밍 규칙
- [ ] FileNamer.kt 생성
- [ ] 파일명 템플릿: `{stream}_{epochMs}_{seq}.{ext}`
- [ ] 디렉토리 구조: `{deviceId}/{sessionId}/`
- [ ] 임시 파일(.tmp) 처리
- [ ] 파일명 파싱 및 검증

#### Phase 12: 스토리지 관리 기초
- [ ] StorageManager.kt 생성
- [ ] 내부 저장소 경로 관리 (context.filesDir)
- [ ] MediaStore 통합 (Android 10+)
- [ ] 디스크 공간 체크 (80% 임계값)
- [ ] 세션 폴더 생성/삭제

#### Phase 13: 에러 모델 및 분류 체계
- [ ] ErrorType enum (SENSOR, BUFFER, UPLOAD, PERMISSION, STORAGE, NETWORK)
- [ ] ErrorSeverity enum (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- [ ] ErrorRecord 데이터 클래스
  - timestamp (UTC + elapsed)
  - type, severity
  - message, stackTrace
  - context (sessionId, sensor, etc.)

#### Phase 14: 에러 로거 - 인메모리 버퍼
- [ ] ErrorLogger.kt 싱글톤 생성
- [ ] Ring buffer (최대 1000개)
- [ ] Thread-safe 로깅 (synchronized/Mutex)
- [ ] 심각도 필터링
- [ ] 중복 에러 감지 (연속 5회 → 1회로 축약)

#### Phase 15: 에러 로거 - 파일 저장
- [ ] 에러 로그 파일 포맷: NDJSON
- [ ] 파일 경로: `{deviceId}/{sessionId}/errors.jsonl`
- [ ] 로테이션 정책 (10MB 또는 1만 건)
- [ ] 백그라운드 스레드 flush
- [ ] 앱 크래시 시 emergency flush

#### Phase 16: 에러 로거 - 업로드 통합
- [ ] 에러 로그도 청크 단위 업로드
- [ ] 에러 스트림 타입: "errors"
- [ ] 우선순위: 일반 센서 데이터보다 높음
- [ ] 실시간 에러 알림 (critical만)

#### Phase 17: Compose 기본 테마 및 디자인 시스템
- [ ] Material3 테마 생성
- [ ] 컬러 팔레트 (Light/Dark)
- [ ] Typography 정의
- [ ] Shapes 정의
- [ ] 공통 Composable (Card, Button, TextField)

#### Phase 18: 네비게이션 설정
- [ ] Compose Navigation 의존성
- [ ] NavHost 설정
- [ ] 화면 Routes enum:
  - LIVE, SESSIONS, UPLOADS, SETTINGS, DIAGNOSTICS
- [ ] BottomNavigationBar
- [ ] 딥링크 준비

#### Phase 19: 설정 관리 (DataStore)
- [ ] DataStore Preferences 의존성
- [ ] SettingsRepository 생성
- [ ] 설정 항목:
  - 샘플링율 (ACC, GYRO, etc.)
  - 청크 길이 (초)
  - 파일 포맷 (protobuf/csv/ndjson)
  - 업로드 정책 (WiFi only, Charging only)
  - 서버 엔드포인트
  - 인증 토큰
  - 로그 레벨
- [ ] Flow<Settings> 제공

#### Phase 20: 디버그 로깅 시스템
- [ ] Timber 라이브러리 통합
- [ ] Custom DebugTree (릴리스 빌드 비활성화)
- [ ] 로그 태그 규칙 (클래스명 기반)
- [ ] 파일 로깅 옵션 (디버그 빌드만)
- [ ] Logcat 필터 가이드 문서

---

### 📡 **Phase 21-90: 센서 데이터 수집 시스템**

#### Phase 21: 센서 추상화 인터페이스
- [ ] SensorSource 인터페이스 정의
  - `start(samplingRate: Int): Flow<SensorSample>`
  - `stop()`
  - `isAvailable(): Boolean`
  - `getInfo(): SensorInfo`
- [ ] SensorSample sealed class
- [ ] SensorInfo (name, type, vendor, maxRange, resolution)

#### Phase 22: 가속도계 소스 (AccSource)
- [ ] SensorManager 초기화
- [ ] TYPE_ACCELEROMETER 리스너 등록
- [ ] 샘플링율: SENSOR_DELAY_FASTEST / 커스텀 마이크로초
- [ ] AccSample(elapsed_ns, ax, ay, az, utc_epoch_ms)
- [ ] Flow 기반 데이터 스트림
- [ ] 드롭 카운터 (이벤트 큐 오버플로우)

#### Phase 23: 자이로스코프 소스 (GyroSource)
- [ ] TYPE_GYROSCOPE 리스너
- [ ] GyroSample(elapsed_ns, gx, gy, gz, utc_epoch_ms)
- [ ] 단위: rad/s
- [ ] 바이어스 보정 옵션 (평균값 제거)

#### Phase 24: 회전 벡터 소스 (RotVecSource)
- [ ] TYPE_ROTATION_VECTOR 리스너
- [ ] RotSample(elapsed_ns, qx, qy, qz, qw, roll, pitch, yaw)
- [ ] Quaternion 정규화
- [ ] Euler 각도 계산 (ZYX 순서)
- [ ] 헤딩 정확도 (경우에 따라 제공)

#### Phase 25: 게임 회전 벡터 소스
- [ ] TYPE_GAME_ROTATION_VECTOR (자기장 제외)
- [ ] 드리프트 최소화
- [ ] VR/AR 앱 호환성

#### Phase 26: 지자기 회전 벡터 소스
- [ ] TYPE_GEOMAGNETIC_ROTATION_VECTOR
- [ ] 자기장 간섭 필터링

#### Phase 27: 중력 센서 소스 (GravitySource)
- [ ] TYPE_GRAVITY
- [ ] GravitySample(elapsed_ns, gx, gy, gz)
- [ ] 중력 방향 단위 벡터

#### Phase 28: 선형 가속도 소스 (LinearAccSource)
- [ ] TYPE_LINEAR_ACCELERATION (중력 제외)
- [ ] LinearAccSample(elapsed_ns, lax, lay, laz)
- [ ] 충격 감지 로직 (임계값)

#### Phase 29: 자기장 센서 소스 (MagSource)
- [ ] TYPE_MAGNETIC_FIELD
- [ ] MagSample(elapsed_ns, mx, my, mz, utc_epoch_ms)
- [ ] 단위: μT (마이크로테슬라)
- [ ] 자기장 세기 계산 (norm)

#### Phase 30: 보행 감지 센서
- [ ] TYPE_STEP_DETECTOR (이벤트 기반)
- [ ] StepEvent(elapsed_ns, utc_epoch_ms)
- [ ] 걷기/뛰기 분류 (가속도 패턴)

#### Phase 31: 보행 계수 센서
- [ ] TYPE_STEP_COUNTER (누적 카운트)
- [ ] StepCountSample(elapsed_ns, count, delta)
- [ ] 재부팅 후 리셋 처리

#### Phase 32: 낙하 감지 센서
- [ ] TYPE_SIGNIFICANT_MOTION
- [ ] SignificantMotionEvent (one-shot)
- [ ] 낙하 이벤트 마킹 (세션 메타데이터)

#### Phase 33: 근접 센서 소스
- [ ] TYPE_PROXIMITY
- [ ] ProximitySample(elapsed_ns, distance_cm, is_near)
- [ ] 스크린 on/off 연동

#### Phase 34: 조도 센서 소스
- [ ] TYPE_LIGHT
- [ ] LightSample(elapsed_ns, lux)
- [ ] 주변 밝기 자동 조정 (UI 디밍)

#### Phase 35: 기압계 소스 (PressureSource)
- [ ] TYPE_PRESSURE
- [ ] PressureSample(elapsed_ns, hPa, utc_epoch_ms)
- [ ] 고도 추정 (해수면 기압 기준)

#### Phase 36: 주변 온도 센서
- [ ] TYPE_AMBIENT_TEMPERATURE
- [ ] AmbientTempSample(elapsed_ns, celsius)
- [ ] 1초 샘플링

#### Phase 37: 상대 습도 센서
- [ ] TYPE_RELATIVE_HUMIDITY
- [ ] HumiditySample(elapsed_ns, percent)
- [ ] 이슬점 계산

#### Phase 38: 심박수 센서 (지원 기기)
- [ ] TYPE_HEART_RATE
- [ ] HeartRateSample(elapsed_ns, bpm, accuracy)
- [ ] PPG 신호 품질 지표

#### Phase 39: 심박 변이도 센서
- [ ] TYPE_HEART_BEAT (이벤트)
- [ ] HeartBeatEvent(elapsed_ns, confidence)
- [ ] RR 간격 계산

#### Phase 40: 마이크 소스 - AudioRecord 설정
- [ ] AudioRecord 초기화
  - 샘플링율: 48000 Hz
  - 채널: MONO
  - 인코딩: PCM_16BIT
  - 버퍼 크기: 20ms 프레임 (1920 샘플)
- [ ] 권한 체크 (RECORD_AUDIO)
- [ ] 오디오 포커스 관리

#### Phase 41: 마이크 소스 - PCM 데이터 수집
- [ ] AudioRecord.read() 루프
- [ ] ByteBuffer 순환 버퍼
- [ ] 프레임 단위 타임스탬프
- [ ] 언더런 감지 및 카운팅

#### Phase 42: 마이크 소스 - 음압 레벨 계산
- [ ] RMS (Root Mean Square) 계산
- [ ] dBFS (Decibels Full Scale)
- [ ] Peak 레벨
- [ ] AudioMeta(elapsed_ns_start, elapsed_ns_end, rms_dbfs, peak_dbfs, frame_count)

#### Phase 43: GPS 소스 - LocationManager 설정
- [ ] LocationManager 초기화
- [ ] GPS_PROVIDER + FUSED_PROVIDER
- [ ] 위치 권한 체크 (FINE + COARSE)
- [ ] 업데이트 간격: 1초 (고정밀) / 10초 (절전)

#### Phase 44: GPS 소스 - 위치 데이터 수집
- [ ] LocationSample 모델:
  - elapsed_ns, utc_epoch_ms
  - latitude, longitude
  - altitude, accuracy
  - bearing, speed
  - provider (GPS/Network/Fused)
- [ ] NMEA 로깅 (옵션)

#### Phase 45: 배터리 상태 소스
- [ ] BatteryManager.EXTRA_LEVEL, EXTRA_SCALE
- [ ] BroadcastReceiver (ACTION_BATTERY_CHANGED)
- [ ] BatterySample:
  - elapsed_ns
  - battery_pct
  - battery_temp_c (EXTRA_TEMPERATURE / 10.0)
  - voltage_mv, current_ma
  - status (충전/방전), health

#### Phase 46: 열 상태 소스
- [ ] PowerManager.getCurrentThermalStatus()
- [ ] ThermalStatusSample:
  - elapsed_ns
  - status (NONE/LIGHT/MODERATE/SEVERE/CRITICAL/EMERGENCY)
  - status_code (0-5)
- [ ] Thermal throttling 이벤트 감지

#### Phase 47: CPU 사용률 모니터링
- [ ] /proc/stat 파싱
- [ ] CpuUsageSample:
  - elapsed_ns
  - total_usage_pct
  - per_core_usage (배열)
- [ ] 앱 전용 CPU 사용률 (/proc/self/stat)

#### Phase 48: 메모리 사용량 모니터링
- [ ] ActivityManager.getMemoryInfo()
- [ ] Debug.MemoryInfo
- [ ] MemorySample:
  - elapsed_ns
  - total_mem_mb, avail_mem_mb
  - app_pss_mb, app_private_dirty_mb
  - low_memory_flag

#### Phase 49: 네트워크 상태 모니터링
- [ ] ConnectivityManager.NetworkCallback
- [ ] NetworkSample:
  - elapsed_ns
  - type (WiFi/Cellular/None)
  - is_metered, is_connected
  - wifi_ssid (권한 있을 때)
  - signal_strength_dbm

#### Phase 50: 카메라 메타데이터 수집
- [ ] Camera2 CaptureResult 리스너
- [ ] CameraMetaSample:
  - elapsed_ns
  - exposure_time_ns, iso, aperture
  - focal_length, focus_distance
  - white_balance, flash_mode
- [ ] 이미지 미포함 (메타만)

#### Phase 51: 카메라 스냅샷 (옵션)
- [ ] CameraX ImageCapture
- [ ] 주기: 0.1~1 Hz (설정 가능)
- [ ] JPEG 압축 (품질 85)
- [ ] 파일명: `snapshot_{epochMs}.jpg`
- [ ] 썸네일 생성 (200x200)

#### Phase 52: 디스플레이 상태 센서
- [ ] 화면 on/off 이벤트 (ACTION_SCREEN_ON/OFF)
- [ ] 밝기 레벨
- [ ] 화면 회전 (orientation)
- [ ] DisplaySample(elapsed_ns, is_on, brightness, rotation)

#### Phase 53: 센서 가용성 체크
- [ ] 모든 센서 소스에 isAvailable() 구현
- [ ] SensorManager.getSensorList() 조회
- [ ] 기기별 센서 매트릭스 생성
- [ ] 설정에서 비활성 센서 숨김

#### Phase 54: 센서 캘리브레이션 UI
- [ ] 가속도계 영점 조정
- [ ] 자이로스코프 바이어스 측정 (정지 상태 30초)
- [ ] 자기장 센서 8자 보정
- [ ] 캘리브레이션 파일 저장

#### Phase 55: 센서 품질 지표
- [ ] 드롭률 계산 (expected vs actual)
- [ ] 레이턴시 측정 (event.timestamp vs process time)
- [ ] 지터 분석 (샘플 간격 표준편차)
- [ ] QualityMetrics(sensor, drop_rate, latency_ms, jitter_ms)

#### Phase 56: 센서 퓨전 - Madgwick 필터 (옵션)
- [ ] ACC + GYRO + MAG → 고정밀 자세 추정
- [ ] 베타 파라미터 튜닝
- [ ] FusedOrientation(roll, pitch, yaw, qx, qy, qz, qw)

#### Phase 57: 센서 퓨전 - Complementary 필터
- [ ] 경량 ACC + GYRO 융합
- [ ] 알파 파라미터 (0.98 기본)
- [ ] 드리프트 보정

#### Phase 58: 이벤트 마커 시스템
- [ ] 사용자 수동 이벤트 마킹 ("낙하", "충격", "정지")
- [ ] EventMarker(elapsed_ns, utc_epoch_ms, label, note)
- [ ] UI 버튼: "Mark Event"
- [ ] events.jsonl 파일 저장

#### Phase 59: 센서 동기화 검증
- [ ] 모든 센서의 elapsed_ns 기준 정렬
- [ ] UTC 타임스탬프 편차 체크 (< 2ms)
- [ ] NTP 동기화 옵션 (네트워크)
- [ ] 동기화 오류 로깅

#### Phase 60: 센서 데이터 시뮬레이터
- [ ] 가짜 센서 신호 생성기:
  - 사인파 (주파수, 진폭)
  - 임펄스 (시간, 크기)
  - 화이트 노이즈
  - 미리 녹음된 패턴 재생
- [ ] 테스트 모드에서 실제 센서 대체
- [ ] 파이프라인 검증용

#### Phase 61-70: 센서별 단위 테스트
- [ ] Phase 61: AccSource 테스트 (Mock SensorManager)
- [ ] Phase 62: GyroSource 테스트
- [ ] Phase 63: RotVecSource 테스트
- [ ] Phase 64: MagSource 테스트
- [ ] Phase 65: PressureSource 테스트
- [ ] Phase 66: MicSource 테스트 (Mock AudioRecord)
- [ ] Phase 67: GPS 테스트 (Mock LocationManager)
- [ ] Phase 68: Battery/Thermal 테스트
- [ ] Phase 69: Camera 메타데이터 테스트
- [ ] Phase 70: 모든 센서 통합 테스트

#### Phase 71-80: 센서 성능 최적화
- [ ] Phase 71: 센서 리스너 스레드 최적화 (HandlerThread)
- [ ] Phase 72: 배치 모드 활용 (센서 FIFO)
- [ ] Phase 73: Wake lock 최소화
- [ ] Phase 74: CPU affinity 설정 (고성능 코어)
- [ ] Phase 75: 메모리 풀링 (객체 재사용)
- [ ] Phase 76: JNI 네이티브 코드 (고주파 센서)
- [ ] Phase 77: 센서 샘플링 동적 조정 (배터리/열)
- [ ] Phase 78: 백그라운드 센서 제한 (Android 12+)
- [ ] Phase 79: 센서 전력 소모 프로파일링
- [ ] Phase 80: 센서 드롭 최소화 전략

#### Phase 81-85: 센서 에러 처리
- [ ] Phase 81: 센서 연결 끊김 감지 및 재연결
- [ ] Phase 82: 센서 정확도 변화 모니터링
- [ ] Phase 83: 센서 하드웨어 오류 감지
- [ ] Phase 84: 센서 권한 거부 처리
- [ ] Phase 85: 센서별 에러 로깅 및 복구

#### Phase 86-90: 추가 센서 및 확장
- [ ] Phase 86: Bluetooth 센서 통합 (외부 센서)
- [ ] Phase 87: USB 센서 통합 (OTG)
- [ ] Phase 88: 웨어러블 센서 연동 (Wear OS)
- [ ] Phase 89: 센서 플러그인 아키텍처
- [ ] Phase 90: 센서 데이터 검증 및 이상치 제거

---

### 💾 **Phase 91-130: 버퍼링 및 스토리지 시스템**

#### Phase 91: 링 버퍼 설계
- [ ] Lock-free ring buffer (Disruptor 패턴)
- [ ] 센서별 독립 버퍼 (크기: 10초 분량)
- [ ] Producer-Consumer 패턴
- [ ] 백프레셔 처리 (드롭 vs 블로킹)

#### Phase 92: 채널 기반 스트리밍
- [ ] Kotlin Flow + Channel
- [ ] BufferOverflow 전략 (DROP_OLDEST)
- [ ] 버퍼 용량 설정 (1000 샘플)
- [ ] Flow 변환 및 필터링

#### Phase 93: 세션 관리자
- [ ] SessionManager.kt 싱글톤
- [ ] 세션 ID 생성 (UUID + timestamp)
- [ ] 세션 상태: IDLE, RECORDING, PAUSED, STOPPED
- [ ] 세션 메타데이터 관리

#### Phase 94: Manifest 파일 생성
- [ ] manifest_{sessionId}.json
- [ ] 내용:
  - device_id, session_id
  - started_at, ended_at
  - sensors: [{name, type, rate, count}]
  - device_info: {model, sdk, manufacturer}
  - time_base: {t0_utc_ms, t0_elapsed_ns}
- [ ] JSON 직렬화 (kotlinx.serialization)

#### Phase 95: 청크 라이터 인터페이스
- [ ] ChunkWriter 인터페이스:
  - `write(samples: List<Sample>, file: File)`
  - `flush()`
  - `close()`
- [ ] 구현체: ProtobufWriter, CsvWriter, NdjsonWriter

#### Phase 96: Protobuf 청크 라이터
- [ ] AccChunk.writeTo(OutputStream)
- [ ] Zstd 압축 래퍼
- [ ] 파일명: `acc_{epochMs}_{seq}.pb.zst`
- [ ] 청크 크기 목표: 1-8 MB

#### Phase 97: CSV 청크 라이터
- [ ] CSV 헤더 자동 생성
- [ ] acc.csv: elapsed_ns,ax,ay,az,utc_epoch_ms
- [ ] Gzip 압축
- [ ] 디버깅용 (기본 비활성화)

#### Phase 98: NDJSON 청크 라이터
- [ ] 한 줄에 하나의 JSON 객체
- [ ] 환경 센서(배터리, 열, 네트워크) 전용
- [ ] env_{epochMs}_{seq}.jsonl
- [ ] kotlinx.serialization.json

#### Phase 99: 마이크 PCM 청크 라이터
- [ ] PCM 16-bit raw data
- [ ] Zstd 압축: mic_{epochMs}_{seq}.pcm.zst
- [ ] 메타데이터 분리: mic_{epochMs}_{seq}_meta.json
  - frame_count, rms_dbfs, peak_dbfs
  - elapsed_ns_start, elapsed_ns_end

#### Phase 100: 청크 시퀀스 관리
- [ ] 스트림별 시퀀스 카운터 (AtomicInteger)
- [ ] 시퀀스 갭 감지
- [ ] 청크 순서 검증
- [ ] 시퀀스 리셋 (세션 종료 시)

#### Phase 101: 청크 타이머
- [ ] N초(10초 기본)마다 flush 트리거
- [ ] ScheduledExecutorService 또는 Flow.chunked()
- [ ] 타이머 일시정지/재개
- [ ] 세션 종료 시 즉시 flush

#### Phase 102: 버퍼 모니터링
- [ ] 버퍼 사용률 추적 (%)
- [ ] 80% 초과 시 경고 로그
- [ ] 95% 초과 시 샘플링율 완화
- [ ] 버퍼 오버플로우 카운터

#### Phase 103: 임시 파일 관리
- [ ] .tmp 확장자로 쓰기 중
- [ ] 완료 후 rename (atomic)
- [ ] 앱 재시작 시 .tmp 파일 복구 또는 삭제
- [ ] 손상 파일 격리 (.corrupted)

#### Phase 104: 청크 무결성 검증
- [ ] 청크 쓰기 후 SHA-256 계산
- [ ] 해시를 별도 파일 저장: `{chunk}.sha256`
- [ ] 업로드 전 검증
- [ ] 손상 청크 재생성 또는 스킵

#### Phase 105: 디스크 쿼터 관리
- [ ] 최대 저장 용량 설정 (10GB 기본)
- [ ] 디스크 80% 임계값
- [ ] 오래된 세션 자동 삭제 (FIFO)
- [ ] 사용자 확인 옵션

#### Phase 106: 세션 아카이브
- [ ] 세션 종료 후 내부 저장소 → MediaStore 이동
- [ ] ZIP 압축 옵션
- [ ] 아카이브 파일명: `session_{sessionId}_{timestamp}.zip`
- [ ] Downloads 폴더 또는 앱 전용 폴더

#### Phase 107: 세션 내보내기
- [ ] SAF (Storage Access Framework) 통합
- [ ] 사용자가 위치 선택
- [ ] 세션 전체 또는 특정 스트림만
- [ ] 진행률 표시

#### Phase 108: 세션 삭제
- [ ] 세션 폴더 재귀 삭제
- [ ] 메타데이터 DB 업데이트
- [ ] Undo 기능 (30초 유예)
- [ ] 휴지통 개념 (소프트 삭제)

#### Phase 109: 세션 목록 UI
- [ ] Room DB 스키마:
  - Session(id, deviceId, startedAt, endedAt, fileCount, sizeMb, uploadStatus)
- [ ] DAO: getAll(), getById(), insert(), delete()
- [ ] ViewModel + StateFlow
- [ ] LazyColumn with SessionCard

#### Phase 110: 세션 상세 화면
- [ ] 센서별 청크 목록
- [ ] 청크 크기, 해시, 업로드 상태
- [ ] 재업로드 버튼
- [ ] 내보내기/삭제 버튼
- [ ] 미리보기 (CSV 샘플)

#### Phase 111: 파일 포맷 변환기
- [ ] Protobuf → CSV 변환
- [ ] CSV → Protobuf 변환
- [ ] 배치 변환 UI
- [ ] 변환 진행률

#### Phase 112: 데이터 검증 툴
- [ ] 청크 무결성 일괄 검사
- [ ] 타임스탬프 연속성 검증
- [ ] 센서 데이터 범위 체크 (이상치)
- [ ] 검증 리포트 생성

#### Phase 113-120: 스토리지 최적화
- [ ] Phase 113: 청크 병합 (작은 파일 → 큰 파일)
- [ ] Phase 114: 스마트 압축 (용량 vs 속도)
- [ ] Phase 115: 중복 제거 (동일 해시)
- [ ] Phase 116: 인덱스 파일 (.idx) 생성
- [ ] Phase 117: 메모리 매핑 I/O (큰 파일)
- [ ] Phase 118: 비동기 I/O (Kotlin IO)
- [ ] Phase 119: 파일 시스템 캐시 최적화
- [ ] Phase 120: SSD 최적화 (TRIM 지원)

#### Phase 121-130: 버퍼 에러 처리 및 복구
- [ ] Phase 121: 디스크 풀 에러 처리
- [ ] Phase 122: 쓰기 권한 에러 처리
- [ ] Phase 123: 파일 손상 감지 및 복구
- [ ] Phase 124: 세션 손실 방지 (체크포인트)
- [ ] Phase 125: 버퍼 오버플로우 soft landing
- [ ] Phase 126: I/O 병목 감지
- [ ] Phase 127: 스토리지 성능 프로파일링
- [ ] Phase 128: 외부 저장소 마운트/언마운트 처리
- [ ] Phase 129: 암호화 저장소 옵션 (Android Keystore)
- [ ] Phase 130: 버퍼 시스템 통합 테스트

---

### 🌐 **Phase 131-170: 업로드 시스템**

#### Phase 131: 업로드 큐 설계
- [ ] UploadQueue.kt (우선순위 큐)
- [ ] 청크 업로드 작업 (ChunkUploadTask)
- [ ] 상태: PENDING, IN_PROGRESS, COMPLETED, FAILED
- [ ] 재시도 카운터 (최대 3회)

#### Phase 132: 업로드 인터페이스
- [ ] Uploader 인터페이스:
  - `upload(chunk: ChunkFile): Result<AckResponse>`
  - `getResumeMap(sessionId: String): Map<String, List<Int>>`
- [ ] 구현체: HttpUploader, WebSocketUploader

#### Phase 133: OkHttp 설정
- [ ] OkHttpClient 싱글톤
- [ ] 타임아웃: connect 10s, read 60s, write 60s
- [ ] 재시도 인터셉터 (지수 백오프)
- [ ] 로깅 인터셉터 (디버그 빌드)

#### Phase 134: HTTP REST 업로더 - 멀티파트
- [ ] POST /ingest/{deviceId}/{sessionId}
- [ ] MultipartBody:
  - meta (application/json): ChunkHeader
  - file (application/octet-stream): 압축 청크
- [ ] Authorization: Bearer <token>
- [ ] 응답: 200 OK + {"ack": true, "received_seq": 42}

#### Phase 135: HTTP REST 업로더 - 청크 전송
- [ ] POST /ingest/chunk (binary only)
- [ ] 헤더:
  - X-Session-Id
  - X-Stream
  - X-Seq
  - X-SHA256
  - Content-Encoding: zstd
- [ ] RequestBody.create()

#### Phase 136: WebSocket 업로더 - 연결 관리
- [ ] WebSocket /ws/ingest
- [ ] 첫 메시지: IngestInit (JSON)
  - device_id, session_id, token
- [ ] Ping/Pong (30초)
- [ ] 재연결 로직 (지수 백오프)

#### Phase 137: WebSocket 업로더 - 프레임 전송
- [ ] ChunkHeader (JSON) + 바이너리 페이로드
- [ ] 프레임 크기: 헤더 512B + 데이터 1-8MB
- [ ] Flow control (서버 ACK 대기)
- [ ] 백프레셔 처리 (큐 적재)

#### Phase 138: WebSocket 업로더 - ACK 처리
- [ ] 서버 → {"type":"ack","stream":"acc","seq":42}
- [ ] ACK 타임아웃 (10초)
- [ ] 미수신 청크 재전송

#### Phase 139: Resume Map 클라이언트
- [ ] GET /resume-map?sessionId=...
- [ ] 응답: {"missing":{"acc":[1,3,5], "gyro":[2]}}
- [ ] 앱 시작/네트워크 복구 시 자동 호출
- [ ] 미수신 청크만 재업로드

#### Phase 140: 청크 해싱 및 검증
- [ ] 청크 업로드 전 SHA-256 계산
- [ ] 헤더에 포함
- [ ] 서버 검증 실패 시 재전송
- [ ] 로컬 해시 캐시

#### Phase 141: 업로드 재시도 로직
- [ ] 지수 백오프: 2초 → 4초 → 8초 → 16초
- [ ] 최대 4회 재시도
- [ ] 네트워크 에러 vs 서버 에러 구분
- [ ] 영구 실패 시 큐에서 제거 (로그)

#### Phase 142: 네트워크 정책
- [ ] WiFi 전용 모드
- [ ] 충전 중 전송 모드
- [ ] 데이터 절약 모드 (압축 레벨 ↑)
- [ ] 설정에서 토글

#### Phase 143: WorkManager 통합
- [ ] UploadWorker.kt (OneTimeWorkRequest)
- [ ] 제약: NetworkType.UNMETERED, Charging (옵션)
- [ ] 입력 데이터: sessionId, chunkPath
- [ ] 결과: Success/Retry/Failure

#### Phase 144: 백그라운드 동기화
- [ ] 주기적 동기화 (PeriodicWorkRequest, 1시간)
- [ ] 대기 중인 청크 일괄 업로드
- [ ] 배터리 최적화 제외 요청 (사용자 동의)

#### Phase 145: 업로드 진행률 추적
- [ ] UploadProgress(sessionId, stream, uploaded, total)
- [ ] Flow<UploadProgress> 제공
- [ ] UI 프로그레스 바 업데이트
- [ ] 알림에도 표시

#### Phase 146: 업로드 알림
- [ ] Foreground Service 알림 업데이트
- [ ] "Uploading 3/10 chunks (30%)"
- [ ] 완료 시 성공/실패 알림
- [ ] 탭하여 상세 화면

#### Phase 147: 에러 로그 우선 업로드
- [ ] errors.jsonl은 일반 센서보다 우선
- [ ] Critical 에러는 즉시 전송
- [ ] 별도 큐 (high priority)

#### Phase 148: 압축 레벨 동적 조정
- [ ] WiFi: Zstd level 3 (균형)
- [ ] Cellular: Zstd level 9 (최대 압축)
- [ ] 배터리 < 20%: 업로드 일시정지

#### Phase 149: 업로드 실패 분석
- [ ] 실패 원인 분류:
  - 네트워크 타임아웃
  - 서버 5xx
  - 클라이언트 4xx (인증 등)
  - 해시 불일치
- [ ] 원인별 카운터
- [ ] UI에 표시

#### Phase 150: 업로드 통계
- [ ] 총 업로드 바이트
- [ ] 평균 속도 (Mbps)
- [ ] 성공/실패 청크 수
- [ ] 재시도 횟수
- [ ] 세션별/전체 통계

#### Phase 151-160: 업로드 최적화
- [ ] Phase 151: HTTP/2 또는 HTTP/3 지원
- [ ] Phase 152: 청크 병렬 업로드 (최대 3개 동시)
- [ ] Phase 153: CDN 엣지 캐싱
- [ ] Phase 154: 업로드 스케줄링 (오프피크)
- [ ] Phase 155: 대역폭 측정 및 adaptive bitrate
- [ ] Phase 156: 청크 분할 (큰 파일 → 작은 조각)
- [ ] Phase 157: Incremental upload (rsync style)
- [ ] Phase 158: 업로드 재개 (Range 헤더)
- [ ] Phase 159: 멀티파트 병렬 전송
- [ ] Phase 160: 업로드 성능 프로파일링

#### Phase 161-170: 업로드 에러 처리 및 복구
- [ ] Phase 161: 네트워크 단절 감지 및 재연결
- [ ] Phase 162: 서버 점검 중 대기
- [ ] Phase 163: 인증 토큰 만료 및 갱신
- [ ] Phase 164: 서버 용량 초과 대응
- [ ] Phase 165: 클라이언트 시간 동기화 (NTP)
- [ ] Phase 166: 업로드 중 앱 종료 처리
- [ ] Phase 167: 기내 모드 자동 일시정지
- [ ] Phase 168: 대용량 파일 특수 처리
- [ ] Phase 169: 업로드 로그 상세 기록
- [ ] Phase 170: 업로드 시스템 통합 테스트

---

### 🎨 **Phase 171-210: UI/UX 개발 (Jetpack Compose)**

#### Phase 171: 메인 스캐폴드
- [ ] MainActivity.kt + Compose setContent
- [ ] Scaffold with TopBar, BottomBar, Content
- [ ] 다크/라이트 테마 토글
- [ ] 시스템 바 색상 조정

#### Phase 172: BottomNavigationBar
- [ ] 5개 탭: Live, Sessions, Uploads, Settings, Diagnostics
- [ ] 아이콘 + 라벨
- [ ] 선택 상태 강조
- [ ] NavController 연동

#### Phase 173: Live 화면 - 레이아웃
- [ ] 스크롤 가능 Column
- [ ] 센서 카드 (LazyColumn 또는 Grid)
- [ ] 상단: 세션 제어 버튼 (Start/Stop/Pause)
- [ ] 하단: 현재 샘플링율/드롭 카운터

#### Phase 174: Live 화면 - 가속도계 카드
- [ ] AccCard Composable
- [ ] 실시간 값: ax, ay, az (소수점 3자리)
- [ ] 스파크라인 차트 (최근 5초)
- [ ] 색상: 축별 구분

#### Phase 175: Live 화면 - 자이로스코프 카드
- [ ] GyroCard
- [ ] gx, gy, gz (rad/s)
- [ ] 스파크라인

#### Phase 176: Live 화면 - 회전 벡터 카드
- [ ] RotationCard
- [ ] Quaternion: qw, qx, qy, qz
- [ ] Euler: roll, pitch, yaw (도)
- [ ] 3D 큐브 시각화 (옵션, 경량)

#### Phase 177: Live 화면 - 오디오 카드
- [ ] AudioCard
- [ ] 실시간 dB 게이지 (원형 또는 선형)
- [ ] Peak hold
- [ ] 마이크 on/off 토글

#### Phase 178: Live 화면 - GPS 카드
- [ ] GpsCard
- [ ] 위도/경도 (소수점 6자리)
- [ ] 고도, 정확도
- [ ] 속도, 방향
- [ ] 미니 맵 (옵션, Google Maps SDK)

#### Phase 179: Live 화면 - 환경 센서 카드
- [ ] EnvCard (Temp, Pressure, Light, Humidity)
- [ ] 게이지 또는 라벨
- [ ] 배터리 아이콘 + %
- [ ] 열 상태 색상 (녹색/노랑/빨강)

#### Phase 180: Live 화면 - 차트 라이브러리
- [ ] Compose용 경량 차트 (Vico 또는 Compose-Charts)
- [ ] LineChart, BarChart
- [ ] 축 라벨, 범례
- [ ] 실시간 업데이트 (Flow)

#### Phase 181: Live 화면 - 이벤트 마커 버튼
- [ ] FloatingActionButton: "Mark Event"
- [ ] 클릭 시 다이얼로그 (라벨 입력)
- [ ] 타임스탬프 자동 기록
- [ ] 세션에 추가

#### Phase 182: Sessions 화면 - 목록
- [ ] LazyColumn of SessionCard
- [ ] SessionCard:
  - 세션 ID (축약)
  - 시작/종료 시간
  - 파일 수, 총 용량 (MB)
  - 업로드 상태 (아이콘: 대기/진행/완료/실패)
- [ ] 클릭 → 상세 화면
- [ ] 스와이프 → 삭제

#### Phase 183: Sessions 화면 - 필터링/정렬
- [ ] 정렬: 최신순, 용량순, 업로드 상태
- [ ] 필터: 미업로드만, 오늘, 이번 주
- [ ] 검색 바 (세션 ID)

#### Phase 184: Session 상세 화면
- [ ] 세션 메타데이터 표시
- [ ] 센서별 청크 리스트 (확장 가능)
- [ ] 청크당: seq, 크기, 해시, 업로드 상태
- [ ] 버튼: 재업로드, 내보내기, 삭제

#### Phase 185: Session 상세 화면 - 청크 미리보기
- [ ] CSV 파일 미리보기 (첫 100줄)
- [ ] Protobuf 디코딩 (간이 뷰어)
- [ ] 오디오 파형 시각화 (PCM)

#### Phase 186: Uploads 화면 - 큐 목록
- [ ] 업로드 대기 청크 리스트
- [ ] 진행 중 청크 (프로그레스 바)
- [ ] 실패 청크 (에러 메시지)
- [ ] 재시도 버튼

#### Phase 187: Uploads 화면 - 통계
- [ ] 총 업로드 바이트, 속도
- [ ] 성공/실패 비율 (파이 차트)
- [ ] 재시도 횟수
- [ ] 평균 레이턴시

#### Phase 188: Settings 화면 - 센서 설정
- [ ] 센서별 샘플링율 슬라이더
- [ ] 센서 on/off 토글
- [ ] 마이크 on/off
- [ ] GPS 정밀도 (High/Balanced/Low)

#### Phase 189: Settings 화면 - 버퍼/파일 설정
- [ ] 청크 길이 (5s / 10s / 30s / 60s)
- [ ] 파일 포맷 (Protobuf / CSV / NDJSON)
- [ ] 압축 레벨 (1-9)
- [ ] 최대 디스크 용량 (GB)

#### Phase 190: Settings 화면 - 업로드 정책
- [ ] WiFi 전용 on/off
- [ ] 충전 중 전송 on/off
- [ ] 백그라운드 동기화 주기 (시간)
- [ ] 병렬 업로드 수 (1-5)

#### Phase 191: Settings 화면 - 서버 설정
- [ ] 엔드포인트 URL (TextField)
- [ ] 인증 토큰 (TextField, 비밀번호 타입)
- [ ] WebSocket/HTTP 선택
- [ ] 연결 테스트 버튼

#### Phase 192: Settings 화면 - 로그/디버그
- [ ] 로그 레벨 (Debug/Info/Warn/Error)
- [ ] 파일 로깅 on/off
- [ ] 로그 내보내기 버튼
- [ ] 개발자 모드 (센서 시뮬레이터)

#### Phase 193: Diagnostics 화면 - 시스템 상태
- [ ] CPU 사용률 (실시간 차트)
- [ ] 메모리 사용량 (앱/시스템)
- [ ] 배터리 온도, %
- [ ] 네트워크 상태 (WiFi/Cellular)

#### Phase 194: Diagnostics 화면 - 센서 품질
- [ ] 센서별 드롭률 (%)
- [ ] 레이턴시 (ms)
- [ ] 지터 (ms)
- [ ] 경고 표시 (드롭률 > 1%)

#### Phase 195: Diagnostics 화면 - 에러 로그
- [ ] 에러 로그 리스트 (최근 100개)
- [ ] 필터: 심각도, 타입
- [ ] 에러 상세 (스택 트레이스)
- [ ] 에러 공유 버튼

#### Phase 196: Diagnostics 화면 - 버퍼 상태
- [ ] 센서별 버퍼 사용률 (%)
- [ ] 경고: 80% 초과 시 노랑, 95% 빨강
- [ ] 버퍼 오버플로우 카운터
- [ ] 버퍼 리셋 버튼

#### Phase 197: 다크 모드 테마
- [ ] Material3 다크 컬러 팔레트
- [ ] 모든 화면 다크 모드 지원
- [ ] 설정에서 토글 (시스템 따름/라이트/다크)
- [ ] 저장 (DataStore)

#### Phase 198: 접근성 (Accessibility)
- [ ] contentDescription 추가
- [ ] 터치 타겟 최소 48dp
- [ ] 색맹 모드 고려 (색상 + 아이콘)
- [ ] TalkBack 테스트

#### Phase 199: 다국어 지원 (i18n)
- [ ] strings.xml (영어)
- [ ] strings-ko.xml (한국어)
- [ ] 주요 UI 문자열 번역
- [ ] 날짜/시간 로케일

#### Phase 200: 애니메이션 및 전환
- [ ] 화면 전환 애니메이션
- [ ] 카드 확장/축소 애니메이션
- [ ] 프로그레스 바 부드러운 업데이트
- [ ] 스파크라인 실시간 애니메이션

#### Phase 201-210: UI 최적화 및 반응성
- [ ] Phase 201: Compose 재구성 최소화 (remember, derivedStateOf)
- [ ] Phase 202: LazyList 키 최적화
- [ ] Phase 203: 이미지 로딩 최적화 (Coil)
- [ ] Phase 204: 스크롤 성능 프로파일링
- [ ] Phase 205: UI 스레드 블로킹 제거
- [ ] Phase 206: 대용량 리스트 페이징 (Paging3)
- [ ] Phase 207: UI 테스트 (Compose Test)
- [ ] Phase 208: 스크린샷 테스트
- [ ] Phase 209: UI/UX 사용성 테스트
- [ ] Phase 210: UI 완성도 점검

---

### ⚙️ **Phase 211-240: 서비스 및 백그라운드 작업**

#### Phase 211: Foreground Service 기본 구조
- [ ] RecorderForegroundService.kt
- [ ] foregroundServiceType: microphone | dataSync
- [ ] onStartCommand, onBind (null)
- [ ] 서비스 시작/정지 인텐트

#### Phase 212: Foreground Service 알림
- [ ] NotificationChannel 생성 (중요도: High)
- [ ] 고정 알림: "Recording Session"
- [ ] 아이콘, 제목, 내용
- [ ] 액션 버튼: Stop, Pause

#### Phase 213: Foreground Service - 센서 수집
- [ ] 서비스 내에서 센서 소스 시작
- [ ] 15+ 센서 병렬 수집
- [ ] Flow 수집 (lifecycleScope)
- [ ] 버퍼에 쓰기

#### Phase 214: Foreground Service - 세션 관리
- [ ] 서비스 시작 시 세션 생성
- [ ] 서비스 정지 시 세션 종료
- [ ] 일시정지/재개 로직
- [ ] 세션 상태 브로드캐스트

#### Phase 215: Wake Lock 관리
- [ ] PARTIAL_WAKE_LOCK (CPU 유지)
- [ ] 획득: 세션 시작 시
- [ ] 해제: 세션 정지 시
- [ ] 배터리 최적화 경고

#### Phase 216: 백그라운드 제한 대응 (Android 12+)
- [ ] Foreground Service 제한 확인
- [ ] 사용자에게 예외 요청 (Settings)
- [ ] Doze 모드 화이트리스트
- [ ] 백그라운드 위치 권한 (필요 시)

#### Phase 217: UploadWorker 기본 구조
- [ ] UploadWorker.kt extends CoroutineWorker
- [ ] doWork() 구현
- [ ] 입력: sessionId, chunkPaths
- [ ] 출력: Result.success/retry/failure

#### Phase 218: UploadWorker - 재시도 정책
- [ ] setBackoffCriteria(LINEAR, 30초)
- [ ] 최대 재시도 횟수 제한
- [ ] 네트워크 에러만 재시도
- [ ] 영구 실패 로깅

#### Phase 219: UploadWorker - 진행률 업데이트
- [ ] setProgress(workDataOf("progress" to X))
- [ ] UI에서 WorkInfo.progress 관찰
- [ ] 알림 업데이트

#### Phase 220: 주기적 동기화 Worker
- [ ] PeriodicWorkRequest (1시간)
- [ ] 제약: Unmetered + Charging (옵션)
- [ ] Resume Map 조회
- [ ] 미업로드 청크 enqueue

#### Phase 221: WorkManager 체인
- [ ] 세션 종료 → 압축 Worker → 업로드 Worker
- [ ] beginWith().then().enqueue()
- [ ] 중간 실패 시 체인 중단

#### Phase 222: 앱 재시작 시 복구
- [ ] 진행 중이던 세션 감지
- [ ] .tmp 파일 복구 또는 삭제
- [ ] 미업로드 청크 자동 enqueue
- [ ] 사용자 선택 (재개/버림)

#### Phase 223: 네트워크 콜백
- [ ] ConnectivityManager.NetworkCallback
- [ ] onAvailable → 업로드 재개
- [ ] onLost → 업로드 일시정지
- [ ] WiFi ↔ Cellular 전환 감지

#### Phase 224: 배터리 최적화 감지
- [ ] PowerManager.isIgnoringBatteryOptimizations()
- [ ] 미등록 시 다이얼로그 (REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
- [ ] 설정 화면 링크

#### Phase 225: Doze 모드 대응
- [ ] AlarmManager.setExactAndAllowWhileIdle() (필요 시)
- [ ] Foreground Service로 우회
- [ ] 테스트: adb shell dumpsys deviceidle

#### Phase 226: 앱 크래시 처리
- [ ] UncaughtExceptionHandler 등록
- [ ] 크래시 로그 파일 저장
- [ ] 다음 시작 시 에러 로그 업로드
- [ ] Firebase Crashlytics 통합 (옵션)

#### Phase 227: 메모리 부족 대응
- [ ] onTrimMemory() 콜백
- [ ] TRIM_MEMORY_RUNNING_CRITICAL 시 버퍼 축소
- [ ] 비필수 센서 일시정지
- [ ] GC 강제 호출 (최후 수단)

#### Phase 228: ANR (Application Not Responding) 방지
- [ ] 무거운 작업 백그라운드 스레드
- [ ] StrictMode 활성화 (디버그)
- [ ] ANR 로그 분석
- [ ] UI 스레드 블로킹 제거

#### Phase 229: 서비스 재시작 정책
- [ ] START_STICKY (시스템이 재시작)
- [ ] START_REDELIVER_INTENT
- [ ] onDestroy에서 정리 작업

#### Phase 230: 백그라운드 위치 권한
- [ ] ACCESS_BACKGROUND_LOCATION (Android 10+)
- [ ] 권한 요청 흐름 (2단계)
- [ ] 사용자 설명 다이얼로그

#### Phase 231-240: 서비스 최적화 및 안정성
- [ ] Phase 231: 서비스 메모리 프로파일링
- [ ] Phase 232: CPU 사용률 최적화
- [ ] Phase 233: 배터리 소모 측정
- [ ] Phase 234: 발열 모니터링 및 스로틀링
- [ ] Phase 235: 장시간 실행 테스트 (24시간+)
- [ ] Phase 236: 네트워크 전환 안정성
- [ ] Phase 237: 다중 세션 동시 처리
- [ ] Phase 238: 서비스 바인딩 (UI 통신)
- [ ] Phase 239: 서비스 생명주기 로깅
- [ ] Phase 240: 서비스 통합 테스트

---

### 🐛 **Phase 241-260: 에러 로깅 및 진단 시스템**

#### Phase 241: 구조화된 에러 로깅
- [ ] ErrorRecord 확장:
  - user_id (옵션)
  - app_version, build_number
  - device_model, os_version
  - free_memory_mb, battery_pct
- [ ] JSON 직렬화

#### Phase 242: 에러 컨텍스트 수집
- [ ] 에러 발생 시 주변 상태 캡처:
  - 활성 세션 ID
  - 현재 센서 상태
  - 버퍼 사용률
  - 네트워크 상태
- [ ] 컨텍스트 스냅샷 저장

#### Phase 243: 스택 트레이스 분석
- [ ] Throwable.stackTraceToString()
- [ ] 중요 프레임 추출 (앱 코드만)
- [ ] 난독화 맵 적용 (릴리스)
- [ ] 중복 스택 해싱

#### Phase 244: 에러 분류 ML
- [ ] 에러 메시지 패턴 매칭
- [ ] 자동 카테고리화
- [ ] 유사 에러 그룹핑
- [ ] 우선순위 자동 할당

#### Phase 245: 에러 알림
- [ ] Critical 에러 즉시 알림
- [ ] 알림 채널: "Errors"
- [ ] 사용자 액션: "View Details"
- [ ] 빈도 제한 (5분에 1회)

#### Phase 246: 에러 대시보드 UI
- [ ] Diagnostics 화면 내 에러 탭
- [ ] 에러 타임라인 차트
- [ ] 심각도별 파이 차트
- [ ] 최근 에러 리스트

#### Phase 247: 에러 검색 및 필터
- [ ] 텍스트 검색 (메시지, 스택)
- [ ] 필터: 타입, 심각도, 날짜
- [ ] 정렬: 시간, 빈도
- [ ] 북마크 기능

#### Phase 248: 에러 공유 및 내보내기
- [ ] 에러 로그 txt/json 내보내기
- [ ] 이메일/Slack 공유
- [ ] GitHub Issue 자동 생성 (옵션)
- [ ] 개인정보 마스킹

#### Phase 249: 에러 재현 도구
- [ ] 에러 발생 조건 기록
- [ ] 재현 스텝 생성
- [ ] 테스트 케이스 자동 생성
- [ ] 회귀 테스트

#### Phase 250: 에러 통계 및 트렌드
- [ ] 일별/주별 에러 수
- [ ] 증가/감소 트렌드
- [ ] 에러율 (에러 / 총 이벤트)
- [ ] Top 10 에러

#### Phase 251: 센서 에러 특화 로깅
- [ ] 센서 초기화 실패
- [ ] 센서 연결 끊김
- [ ] 센서 정확도 저하
- [ ] 센서 하드웨어 오류
- [ ] 자동 복구 시도 기록

#### Phase 252: 버퍼 에러 로깅
- [ ] 버퍼 오버플로우
- [ ] 디스크 풀
- [ ] 쓰기 권한 거부
- [ ] 파일 손상
- [ ] 자동 완화 조치 기록

#### Phase 253: 업로드 에러 로깅
- [ ] 네트워크 타임아웃
- [ ] 서버 에러 (코드, 메시지)
- [ ] 인증 실패
- [ ] 해시 불일치
- [ ] 재시도 이력

#### Phase 254: 성능 에러 로깅
- [ ] ANR 감지
- [ ] 과도한 GC
- [ ] CPU 스로틀링
- [ ] 메모리 누수
- [ ] 배터리 과소모

#### Phase 255: 에러 자동 복구
- [ ] 센서 재시작
- [ ] 버퍼 리셋
- [ ] 업로드 재시도
- [ ] 서비스 재시작
- [ ] 복구 성공/실패 로깅

#### Phase 256: 에러 로그 압축 및 아카이브
- [ ] 7일 이상 로그 압축
- [ ] 30일 이상 로그 삭제
- [ ] 아카이브 파일 생성
- [ ] 클라우드 백업 (옵션)

#### Phase 257: 에러 로그 분석 도구
- [ ] 오프라인 로그 파서
- [ ] 통계 리포트 생성
- [ ] 그래프 시각화
- [ ] 이상치 감지

#### Phase 258: 에러 로그 개인정보 보호
- [ ] PII (개인식별정보) 자동 마스킹
- [ ] 위치 정보 해싱
- [ ] 사용자 동의 확인
- [ ] GDPR 준수

#### Phase 259: 에러 피드백 루프
- [ ] 에러 리포트 → 개발팀
- [ ] 수정 후 재배포
- [ ] 에러 감소 확인
- [ ] 사용자 피드백 수집

#### Phase 260: 에러 시스템 통합 테스트
- [ ] 인위적 에러 주입
- [ ] 복구 메커니즘 검증
- [ ] 로그 무결성 확인
- [ ] 성능 영향 측정

---

### 🧪 **Phase 261-285: 테스팅 및 품질 보증**

#### Phase 261-270: 단위 테스트 (Unit Tests)
- [ ] Phase 261: 센서 소스 테스트 (Mock)
- [ ] Phase 262: 버퍼 시스템 테스트
- [ ] Phase 263: 업로드 시스템 테스트
- [ ] Phase 264: 데이터 모델 직렬화 테스트
- [ ] Phase 265: 압축/해시 유틸리티 테스트
- [ ] Phase 266: 타임스탬프 동기화 테스트
- [ ] Phase 267: 에러 로거 테스트
- [ ] Phase 268: 설정 관리 테스트
- [ ] Phase 269: 파일 네이밍 테스트
- [ ] Phase 270: ViewModel 로직 테스트

#### Phase 271-275: 통합 테스트 (Integration Tests)
- [ ] Phase 271: 센서 → 버퍼 → 파일 파이프라인
- [ ] Phase 272: 파일 → 업로드 → 서버 ACK
- [ ] Phase 273: 세션 생성 → 종료 → 아카이브
- [ ] Phase 274: Resume Map → 재업로드
- [ ] Phase 275: 에러 발생 → 로깅 → 업로드

#### Phase 276-280: UI 테스트 (Compose Test)
- [ ] Phase 276: Live 화면 센서 카드 렌더링
- [ ] Phase 277: Sessions 목록 스크롤/클릭
- [ ] Phase 278: Settings 값 변경 및 저장
- [ ] Phase 279: Diagnostics 차트 업데이트
- [ ] Phase 280: 네비게이션 흐름 테스트

#### Phase 281: End-to-End 테스트
- [ ] 세션 시작 → 1시간 녹화 → 업로드 완료
- [ ] 실제 기기에서 실행
- [ ] 드롭률 < 0.1% 확인
- [ ] 모든 청크 무결성 검증

#### Phase 282: 성능 테스트
- [ ] CPU 프로파일링 (Android Profiler)
- [ ] 메모리 누수 감지 (LeakCanary)
- [ ] 배터리 소모 측정 (Battery Historian)
- [ ] 발열 모니터링

#### Phase 283: 스트레스 테스트
- [ ] 24시간 연속 녹화
- [ ] 네트워크 끊김/복구 반복
- [ ] 앱 재시작 100회
- [ ] 디스크 풀 시나리오

#### Phase 284: 호환성 테스트
- [ ] Android 10, 11, 12, 13, 14 기기
- [ ] 다양한 제조사 (Samsung, Google, Xiaomi 등)
- [ ] 화면 크기 (폰, 태블릿, 폴더블)
- [ ] 센서 가용성 매트릭스

#### Phase 285: 보안 테스트
- [ ] 권한 누락 시나리오
- [ ] 네트워크 스니핑 (TLS 검증)
- [ ] 토큰 노출 취약점
- [ ] 로컬 파일 접근 제어

---

### 🚀 **Phase 286-295: 최적화 및 성능 튜닝**

#### Phase 286: 시작 시간 최적화
- [ ] App Startup 라이브러리
- [ ] Lazy 초기화
- [ ] Splash 화면 최소화
- [ ] 콜드 스타트 < 2초 목표

#### Phase 287: 메모리 최적화
- [ ] Bitmap 캐싱 최적화
- [ ] 객체 풀링 (센서 샘플)
- [ ] WeakReference 활용
- [ ] 메모리 사용량 < 200MB 목표

#### Phase 288: 네트워크 최적화
- [ ] 청크 크기 최적화 (1-8MB)
- [ ] 압축 레벨 벤치마크
- [ ] HTTP/2 활용
- [ ] 대역폭 adaptive

#### Phase 289: 배터리 최적화
- [ ] JobScheduler vs WorkManager
- [ ] Doze 모드 최적화
- [ ] Wake lock 최소화
- [ ] 센서 샘플링율 동적 조정

#### Phase 290: 파일 I/O 최적화
- [ ] 버퍼 크기 튜닝
- [ ] 비동기 쓰기
- [ ] SSD 최적화 (TRIM)
- [ ] 파일 시스템 캐시

#### Phase 291: UI 렌더링 최적화
- [ ] Compose 재구성 최소화
- [ ] LazyList 키 최적화
- [ ] 애니메이션 60fps 유지
- [ ] OverDraw 제거

#### Phase 292: 센서 샘플링 최적화
- [ ] FIFO 배치 모드
- [ ] 센서 fusion 활용
- [ ] HandlerThread 우선순위
- [ ] 드롭률 최소화

#### Phase 293: ProGuard/R8 난독화
- [ ] 릴리스 빌드 설정
- [ ] 난독화 규칙 (proguard-rules.pro)
- [ ] 맵 파일 저장
- [ ] 크래시 역난독화

#### Phase 294: APK 크기 최적화
- [ ] Resource shrinking
- [ ] Code shrinking
- [ ] 이미지 WebP 변환
- [ ] 미사용 라이브러리 제거
- [ ] APK < 15MB 목표

#### Phase 295: 최종 성능 벤치마크
- [ ] 모든 최적화 통합 테스트
- [ ] 실제 기기 벤치마크 (10종)
- [ ] 성능 리포트 생성
- [ ] 목표 달성 확인

---

### 📚 **Phase 296-300: 문서화 및 배포**

#### Phase 296: 사용자 문서
- [ ] README.md (앱 소개, 기능)
- [ ] 사용 가이드 (스크린샷 포함)
- [ ] FAQ
- [ ] 트러블슈팅 가이드

#### Phase 297: 개발자 문서
- [ ] 아키텍처 문서
- [ ] API 명세 (서버 엔드포인트)
- [ ] 데이터 스키마 (Protobuf, CSV)
- [ ] 확장 가이드 (새 센서 추가)

#### Phase 298: Google Play 배포 준비
- [ ] 앱 아이콘 (적응형)
- [ ] 스크린샷 (5개 이상)
- [ ] 앱 설명 (한글/영문)
- [ ] 개인정보 처리방침
- [ ] 릴리스 노트

#### Phase 299: 베타 테스트
- [ ] Google Play Console 내부 테스트
- [ ] 피드백 수집
- [ ] 버그 수정
- [ ] 성능 개선

#### Phase 300: 정식 출시
- [ ] Google Play 정식 배포
- [ ] 서버 인프라 최종 점검
- [ ] 모니터링 대시보드 설정
- [ ] 출시 공지 및 홍보

---

## 품질 보증 체크리스트

### ✅ 센서 정확도
- [ ] 센서별 샘플링율 정확도 ±1%
- [ ] 타임스탬프 정합 (UTC vs elapsed) 잔차 < 2ms
- [ ] 센서 융합 오차 < 1도 (Euler 각도)
- [ ] GPS 위치 정확도 < 10m (옥외)

### ✅ 데이터 무결성
- [ ] 1시간 세션 드롭률 < 0.1%
- [ ] 청크 SHA-256 검증 100% 통과
- [ ] 타임스탬프 연속성 검증
- [ ] 파일 손상 복구 메커니즘

### ✅ 업로드 신뢰성
- [ ] 업로드 재개 테스트 (기내모드/재부팅) 통과
- [ ] Resume Map 정확도 100%
- [ ] 네트워크 전환 안정성 (WiFi ↔ Cellular)
- [ ] 청크 중복 업로드 0%

### ✅ 성능
- [ ] 앱 시작 시간 < 2초 (콜드)
- [ ] 메모리 사용량 < 200MB (평균)
- [ ] CPU 사용률 < 20% (녹화 중)
- [ ] 배터리 소모 < 10%/시간

### ✅ 안정성
- [ ] 24시간 연속 녹화 크래시 0회
- [ ] ANR 발생 0회
- [ ] 메모리 누수 0건
- [ ] 에러 복구율 > 95%

### ✅ 호환성
- [ ] Android 10-14 호환
- [ ] 10종 이상 기기 테스트
- [ ] 센서 미지원 기기 정상 동작
- [ ] 다양한 화면 크기 지원

### ✅ 보안
- [ ] TLS 1.3 통신
- [ ] 토큰 안전 저장 (EncryptedSharedPreferences)
- [ ] 권한 최소화 원칙
- [ ] 개인정보 보호 (PII 마스킹)

### ✅ 사용성
- [ ] 직관적 UI (사용자 테스트)
- [ ] 접근성 (TalkBack 호환)
- [ ] 다국어 지원 (한/영)
- [ ] 에러 메시지 명확성

---

## 위험 요소 및 대응 전략

### 🔴 고위험

| 위험 | 영향 | 확률 | 대응 전략 |
|------|------|------|----------|
| 센서 드롭 과다 | 데이터 손실 | 중 | 버퍼 크기 증가, 샘플링율 동적 조정 |
| 배터리 과소모 | 사용자 불만 | 높음 | 센서 on/off, 절전 모드, 백그라운드 제한 |
| 네트워크 불안정 | 업로드 실패 | 높음 | Resume Map, 재시도, 로컬 저장 |
| 메모리 부족 | 앱 크래시 | 중 | 메모리 모니터링, Trim, 버퍼 축소 |

### 🟡 중위험

| 위험 | 영향 | 확률 | 대응 전략 |
|------|------|------|----------|
| 디스크 풀 | 세션 손실 | 중 | 쿼터 관리, 자동 삭제, 사용자 경고 |
| 센서 미지원 | 기능 제한 | 높음 | 가용성 체크, fallback, UI 숨김 |
| 서버 다운 | 업로드 지연 | 낮음 | 로컬 큐, 백그라운드 동기화 |
| 권한 거부 | 기능 제한 | 중 | 권한 설명, 필수 권한 구분 |

### 🟢 저위험

| 위험 | 영향 | 확률 | 대응 전략 |
|------|------|------|----------|
| UI 버그 | 사용성 저하 | 낮음 | Compose 테스트, 베타 테스트 |
| 타임존 오류 | 타임스탬프 오차 | 낮음 | UTC 기준, NTP 동기화 |
| 압축 실패 | 용량 증가 | 낮음 | Gzip fallback, 에러 로깅 |

---

## 기술 스택 요약

### 언어 및 프레임워크
- **Kotlin** 1.9+
- **Jetpack Compose** (UI)
- **Coroutines** + **Flow** (비동기)

### 주요 라이브러리
- **Hilt** (의존성 주입)
- **Room** (로컬 DB)
- **DataStore** (설정)
- **WorkManager** (백그라운드 작업)
- **OkHttp** (네트워크)
- **Protobuf** (직렬화)
- **Zstd-JNI** (압축)
- **kotlinx.serialization** (JSON)
- **Accompanist** (권한, 시스템 UI)
- **Vico/Compose-Charts** (차트)
- **CameraX** (카메라)
- **Timber** (로깅)
- **LeakCanary** (디버그)

### 테스팅
- **JUnit 5**
- **MockK**
- **Compose Test**
- **Robolectric**
- **Espresso** (E2E)

### 빌드 및 배포
- **Gradle KTS** (빌드 스크립트)
- **ProGuard/R8** (난독화)
- **Google Play Console**
- **Firebase Crashlytics** (옵션)

---

## 개발 타임라인 (예상)

| Phase 범위 | 기간 | 마일스톤 |
|-----------|------|---------|
| 1-20 | 1개월 | 프로젝트 설정 및 기초 인프라 |
| 21-90 | 3개월 | 센서 데이터 수집 시스템 |
| 91-130 | 2개월 | 버퍼링 및 스토리지 |
| 131-170 | 2개월 | 업로드 시스템 |
| 171-210 | 2개월 | UI/UX 개발 |
| 211-240 | 1.5개월 | 서비스 및 백그라운드 |
| 241-260 | 1개월 | 에러 로깅 |
| 261-285 | 1.5개월 | 테스팅 및 QA |
| 286-295 | 1개월 | 최적화 |
| 296-300 | 0.5개월 | 문서화 및 배포 |
| **총합** | **15-18개월** | **정식 출시** |

---

## 우선순위 기준

### P0 (필수, 출시 차단)
- 모든 Phase 1-20 (인프라)
- Phase 21-45 (핵심 센서: ACC, GYRO, ROT, MIC, GPS, Battery)
- Phase 91-110 (버퍼 및 파일 저장)
- Phase 131-145 (업로드 기본)
- Phase 171-185 (기본 UI)
- Phase 211-220 (Foreground Service, Worker)
- Phase 261-275 (핵심 테스트)

### P1 (중요, 출시 후 1개월)
- Phase 46-60 (추가 센서)
- Phase 111-120 (스토리지 최적화)
- Phase 146-160 (업로드 고급)
- Phase 186-200 (UI 고급)
- Phase 241-255 (에러 로깅)
- Phase 276-285 (QA)

### P2 (개선, 출시 후 3개월)
- Phase 61-90 (센서 확장 및 최적화)
- Phase 121-130 (스토리지 고급)
- Phase 161-170 (업로드 최적화)
- Phase 201-210 (UI 최적화)
- Phase 286-295 (성능 튜닝)

### P3 (선택, 향후 버전)
- 센서 시뮬레이터
- 웨어러블 연동
- 외부 센서 (Bluetooth, USB)
- ML 기반 에러 분류

---

## 다음 단계

1. **Phase 1-20 시작**: 프로젝트 설정 및 기초 인프라 구축
2. **프로토타입 개발**: 1개 센서 (ACC) → 버퍼 → 파일 → 업로드 파이프라인 검증
3. **서버 개발 병행**: REST/WebSocket 엔드포인트 구현
4. **반복 개발**: 2주 스프린트, 센서 추가 및 통합
5. **지속적 테스팅**: 매 Phase 완료 시 단위/통합 테스트
6. **베타 출시**: Phase 280 완료 후 내부 테스트
7. **정식 출시**: Phase 300 완료

---

**작성자**: Claude (AI Assistant)
**검토 필요**: 기술 리드, PM, QA 리드
**업데이트 주기**: 월 1회 또는 주요 마일스톤 시

---

이 계획서는 매우 상세하며, 실제 개발 중 조정이 필요할 수 있습니다. 우선순위와 리소스에 따라 유연하게 적용하시기 바랍니다.
