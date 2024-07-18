# 위버스 스크래퍼
## 개요
VMGO_search(https://team-devfuse.com/vmgo) 에서 사용할 데이터 수집을 위한 위버스 스크래퍼입니다.

## VMGO_search
### 기획의도
- Vlive -> Weverse 이관 후 구 주소 리다이렉트 지원하지 않아 기존에 팬덤이 노션으로 아카이빙 해 온 자료의 유효성이 사라짐.
- Weverse에서 날짜나 아티스트별 서치 지원하지 않아 신규 팬 유입 시 복습이 어려움.
- 기존의 노션 백업 데이터와 Weverse 스크래핑 데이터를 합쳐서 위 불편함 해소, 팬들이 원하는 라이브 영상을 손쉽게 찾을 수 있도록 보강함.

### 아키텍쳐
```mermaid
graph TD
  subgraph 데이터_수집
    style 데이터_수집 stroke:#ff0000,stroke-width:2px
    A[Python 스크래퍼] <--> B[Weverse 사이트]
    A --> C[Google Sheets]
    C --> D[수기 가공]
    D --> E[CSV 파일]
    E --> F[Supabase DB]
  end

    subgraph 웹사이트
    direction TB
    G[Next.js 애플리케이션]
    G --> H[Styled Components]
    G --> I[Supabase API]
    G --> J[Google Analytics]
    I --> F
  end

  subgraph 사용자_인터페이스
    direction TB
    K[사용자] --> L[브라우저]
    L --> N[Vercel]
    N --> G
  end

  subgraph AWS
    direction TB
    subgraph CloudFront
      direction TB
      P[도메인 vmgo.team-devfuse.com] --> N
    end
  end

```

### 데이터 백업 플로우
```mermaid
sequenceDiagram
  autonumber

  actor User as 사용자
  participant Scraper as Python 스크래퍼
  participant Weverse as Weverse 사이트
  participant GoogleSheets as Google Sheets
  participant SupabaseUploader as Supabase

  User->>Scraper: 1. 스크래퍼 RUN
  Scraper->>Weverse: Selenium으로 데이터 스크래핑
  Weverse->>Scraper: 스크래핑한 데이터 응답
  Scraper->>User: 응답 후 자동으로 CSV 다운로드

  User->>GoogleSheets: 2. 스크래핑한 데이터에 tag, desc등 정보 수기로 추가해 백업
  GoogleSheets->>User: 3. 추가할 분량만 CSV 파일로 다운로드

  User->>SupabaseUploader: 4. Supabase 테이블에 CSV 파일 업로드

```
