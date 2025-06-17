import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""


# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)


# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")


# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")


# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")


# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()


# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()


# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Bike Sharing Demand EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (train.csv)", type="csv")
        if not uploaded:
            st.info("train.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded, parse_dates=['datetime'])

        tabs = st.tabs([
            "1. 목적 & 절차",
            "2. 데이터셋 설명",
            "3. 데이터 로드 & 품질 체크",
            "4. Datetime 특성 추출",
            "5. 시각화",
            "6. 상관관계 분석",
            "7. 이상치 제거",
            "8. 로그 변환",
            "9. 세종 인구통계",
            "10. 전국 인구 추이 예측",
            "11. 지역별 인구 변화 분석",
            "12. 지역별 인구 증감 상위 100",
            "13. 지역별 누적 인구 영역 그래프",
            "14. 인구통계 EDA"
        ])

        # 1. 목적 & 분석 절차
        with tabs[0]:
            st.header("🔭 목적 & 분석 절차")
            st.markdown("""
            **목적**: Bike Sharing Demand 데이터셋을 탐색하고,
            다양한 특성이 대여량(count)에 미치는 영향을 파악합니다.

            **절차**:
            1. 데이터 구조 및 기초 통계 확인  
            2. 결측치/중복치 등 품질 체크  
            3. datetime 특성(연도, 월, 일, 시, 요일) 추출  
            4. 주요 변수 시각화  
            5. 변수 간 상관관계 분석  
            6. 이상치 탐지 및 제거  
            7. 로그 변환을 통한 분포 안정화
            """)

        # 2. 데이터셋 설명
        with tabs[1]:
            st.header("🔍 데이터셋 설명")
            st.markdown(f"""
            - **train.csv**: 2011–2012년까지의 시간대별 대여 기록  
            - 총 관측치: {df.shape[0]}개  
            - 주요 변수:
              - **datetime**: 날짜와 시간 (YYYY-MM-DD HH:MM:SS)  
              - **season**: 계절 (1: 봄, 2: 여름, 3: 가을, 4: 겨울)  
              - **holiday**: 공휴일 여부 (0: 평일, 1: 공휴일)  
              - **workingday**: 근무일 여부 (0: 주말/공휴일, 1: 근무일)  
              - **weather**: 날씨 상태  
                - 1: 맑음·부분적으로 흐림  
                - 2: 안개·흐림  
                - 3: 가벼운 비/눈  
                - 4: 폭우/폭설 등  
              - **temp**: 실제 기온 (섭씨)  
              - **atemp**: 체감 온도 (섭씨)  
              - **humidity**: 상대 습도 (%)  
              - **windspeed**: 풍속 (정규화된 값)  
              - **casual**: 비등록 사용자 대여 횟수  
              - **registered**: 등록 사용자 대여 횟수  
              - **count**: 전체 대여 횟수 (casual + registered)
            """)

            st.subheader("1) 데이터 구조 (`df.info()`)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("2) 기초 통계량 (`df.describe()`)")
            numeric_df = df.select_dtypes(include=[np.number])
            st.dataframe(numeric_df.describe())

            st.subheader("3) 샘플 데이터 (첫 5행)")
            st.dataframe(df.head())

        # 3. 데이터 로드 & 품질 체크
        with tabs[2]:
            st.header("📥 데이터 로드 & 품질 체크")
            st.subheader("결측값 개수")
            missing = df.isnull().sum()
            st.bar_chart(missing)

            duplicates = df.duplicated().sum()
            st.write(f"- 중복 행 개수: {duplicates}개")

        # 4. Datetime 특성 추출
        with tabs[3]:
            st.header("🕒 Datetime 특성 추출")
            st.markdown("`datetime` 컬럼에서 연, 월, 일, 시, 요일 등을 추출합니다.")

            df['year'] = df['datetime'].dt.year
            df['month'] = df['datetime'].dt.month
            df['day'] = df['datetime'].dt.day
            df['hour'] = df['datetime'].dt.hour
            df['dayofweek'] = df['datetime'].dt.dayofweek

            st.subheader("추출된 특성 예시")
            st.dataframe(df[['datetime', 'year', 'month', 'day', 'hour',
                             'dayofweek']].head())

            # --- 요일 숫자 → 요일명 매핑 (참고용) ---
            day_map = {
                0: '월요일',
                1: '화요일',
                2: '수요일',
                3: '목요일',
                4: '금요일',
                5: '토요일',
                6: '일요일'
            }
            st.markdown("**(참고) dayofweek 숫자 → 요일**")
            # 중복 제거 후 정렬하여 표시
            mapping_df = pd.DataFrame({
                'dayofweek': list(day_map.keys()),
                'weekday': list(day_map.values())
            })
            st.dataframe(mapping_df, hide_index=True)

        # 5. 시각화
        with tabs[4]:
            st.header("📈 시각화")
            # by 근무일 여부
            st.subheader("근무일 여부별 시간대별 평균 대여량")
            fig1, ax1 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='workingday', data=df,
                          ax=ax1)
            ax1.set_xlabel("Hour");
            ax1.set_ylabel("Average Count")
            st.pyplot(fig1)
            st.markdown(
                "> **해석:** 근무일(1)은 출퇴근 시간(7 ~ 9시, 17 ~ 19시)에 대여량이 급증하는 반면,\n"
                "비근무일(0)은 오후(11 ~ 15시) 시간대에 대여량이 상대적으로 높게 나타납니다."
            )

            # by 요일
            st.subheader("요일별 시간대별 평균 대여량")
            fig2, ax2 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='dayofweek', data=df, ax=ax2)
            ax2.set_xlabel("Hour");
            ax2.set_ylabel("Average Count")
            st.pyplot(fig2)
            st.markdown(
                "> **해석:** 평일(월 ~ 금)은 출퇴근 피크가 두드러지고,\n"
                "주말(토~일)은 오전 중반(10 ~ 14시)에 대여량이 더 고르게 분포하는 경향이 있습니다."
            )

            # by 시즌
            st.subheader("시즌별 시간대별 평균 대여량")
            fig3, ax3 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='season', data=df, ax=ax3)
            ax3.set_xlabel("Hour");
            ax3.set_ylabel("Average Count")
            st.pyplot(fig3)
            st.markdown(
                "> **해석:** 여름(2)과 가을(3)에 전반적으로 대여량이 높고,\n"
                "겨울(4)은 전 시간대에 걸쳐 대여량이 낮게 나타납니다."
            )

            # by 날씨
            st.subheader("날씨 상태별 시간대별 평균 대여량")
            fig4, ax4 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='weather', data=df, ax=ax4)
            ax4.set_xlabel("Hour");
            ax4.set_ylabel("Average Count")
            st.pyplot(fig4)
            st.markdown(
                "> **해석:** 맑음(1)은 전 시간대에서 대여량이 가장 높으며,\n"
                "안개·흐림(2), 가벼운 비/눈(3)에선 다소 감소하고, 심한 기상(4)에서는 크게 떨어집니다."
            )

        # 6. 상관관계 분석
        with tabs[5]:
            st.header("🔗 상관관계 분석")
            # 관심 피처만 선택
            features = ['temp', 'atemp', 'casual', 'registered', 'humidity',
                        'windspeed', 'count']
            corr_df = df[features].corr()

            # 상관계수 테이블 출력
            st.subheader("📊 피처 간 상관계수")
            st.dataframe(corr_df)

            # 히트맵 시각화
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(corr_df, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
            ax.set_xlabel("")  # 축 이름 제거
            ax.set_ylabel("")
            st.pyplot(fig)
            st.markdown(
                "> **해석:**\n"
                "- `count`는 `registered` (r≈0.99) 및 `casual` (r≈0.67)와 강한 양의 상관관계를 보입니다.\n"
                "- `temp`·`atemp`와 `count`는 중간 정도의 양의 상관관계(r≈0.4~0.5)를 나타내며, 기온이 높을수록 대여량이 증가함을 시사합니다.\n"
                "- `humidity`와 `windspeed`는 약한 음의 상관관계(r≈-0.2~-0.3)를 보여, 습도·풍속이 높을수록 대여량이 다소 감소합니다."
            )

        # 7. 이상치 제거
        with tabs[6]:
            st.header("🚫 이상치 제거")
            # 평균·표준편차 계산
            mean_count = df['count'].mean()
            std_count = df['count'].std()
            # 상한치: 평균 + 3*표준편차
            upper = mean_count + 3 * std_count

            st.markdown(f"""
                        - **평균(count)**: {mean_count:.2f}  
                        - **표준편차(count)**: {std_count:.2f}  
                        - **이상치 기준**: `count` > 평균 + 3×표준편차 = {upper:.2f}  
                          (통계학의 68-95-99.7 법칙(Empirical rule)에 따라 평균에서 3σ를 벗어나는 관측치는 전체의 약 0.3%로 극단치로 간주)
                        """)
            df_no = df[df['count'] <= upper]
            st.write(f"- 이상치 제거 전: {df.shape[0]}개, 제거 후: {df_no.shape[0]}개")

        # 8. 로그 변환
        with tabs[7]:
            st.header("🔄 로그 변환")
            st.markdown("""
                **로그 변환 맥락**  
                - `count` 변수는 오른쪽으로 크게 치우친 분포(skewed distribution)를 가지고 있어,  
                  통계 분석 및 모델링 시 정규성 가정이 어렵습니다.  
                - 따라서 `Log(Count + 1)` 변환을 통해 분포의 왜도를 줄이고,  
                  중앙값 주변으로 데이터를 모아 해석력을 높입니다.
                """)

            # 변환 전·후 분포 비교
            fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 4))

            # 원본 분포
            sns.histplot(df['count'], kde=True, ax=axes[0])
            axes[0].set_title("Original Count Distribution")
            axes[0].set_xlabel("Count")
            axes[0].set_ylabel("Frequency")

            # 로그 변환 분포
            df['log_count'] = np.log1p(df['count'])
            sns.histplot(df['log_count'], kde=True, ax=axes[1])
            axes[1].set_title("Log(Count + 1) Distribution")
            axes[1].set_xlabel("Log(Count + 1)")
            axes[1].set_ylabel("Frequency")

            st.pyplot(fig)

            st.markdown("""
                > **그래프 해석:**  
                > - 왼쪽: 원본 분포는 한쪽으로 긴 꼬리를 가진 왜곡된 형태입니다.  
                > - 오른쪽: 로그 변환 후 분포는 훨씬 균형잡힌 형태로, 중앙값 부근에 데이터가 집중됩니다.  
                > - 극단치의 영향이 완화되어 이후 분석·모델링 안정성이 높아집니다.
                """)

        # 9. 세종 인구통계
        with tabs[8]:
            st.header("📈 세종 인구통계 분석")

            pop_file = st.file_uploader("population_trends.csv 파일 업로드", type="csv", key="sejong_pop_file")
            if pop_file:
                df_pop = pd.read_csv(pop_file)

                # 1. '세종' 지역 필터링
                sejong_df = df_pop[df_pop['행정구역'].str.contains("세종")].copy()

                # 2. 결측치 '-' → 0으로 변환
                sejong_df.replace('-', '0', inplace=True)

                # 3. 숫자형 열 변환
                cols_to_numeric = ['인구', '출생아수(명)', '사망자수(명)']
                for col in cols_to_numeric:
                    sejong_df[col] = pd.to_numeric(sejong_df[col], errors='coerce').fillna(0)

                st.subheader("📋 전처리된 세종시 데이터 (일부)")
                st.dataframe(sejong_df.head())

                st.subheader("🧾 데이터프레임 구조 (df.info())")
                buffer = io.StringIO()
                sejong_df.info(buf=buffer)
                st.text(buffer.getvalue())

                st.subheader("📊 요약 통계 (df.describe())")
                st.dataframe(sejong_df.describe())
            else:
                st.info("population_trends.csv 파일을 업로드해주세요.")

        # 10. 전국 인구 추이 예측
        with tabs[9]:
            st.header("📈 National Population Trend Forecast")

            pop_file = st.file_uploader("Upload population_trends.csv", type="csv", key="national_pop_file")
            if pop_file:
                df_pop = pd.read_csv(pop_file)

                # '-' 결측치 처리
                df_pop.replace('-', '0', inplace=True)
                df_pop['인구'] = pd.to_numeric(df_pop['인구'], errors='coerce').fillna(0)
                df_pop['출생아수(명)'] = pd.to_numeric(df_pop['출생아수(명)'], errors='coerce').fillna(0)
                df_pop['사망자수(명)'] = pd.to_numeric(df_pop['사망자수(명)'], errors='coerce').fillna(0)

                # '전국' 필터링
                national_df = df_pop[df_pop['지역'] == '전국'].copy()
                national_df['연도'] = pd.to_numeric(national_df['연도'], errors='coerce')
                national_df.sort_values('연도', inplace=True)

                # 최근 3년 평균 인구 증가량 계산
                recent = national_df.tail(3)
                avg_change = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()

                # 2035년 인구 예측
                last_year = national_df['연도'].max()
                last_pop = national_df[national_df['연도'] == last_year]['인구'].values[0]
                years_ahead = 2035 - last_year
                pred_2035 = int(last_pop + avg_change * years_ahead)

                # 예측 데이터 추가
                forecast_df = national_df[['연도', '인구']].copy()
                forecast_df.loc[len(forecast_df)] = [2035, pred_2035]

                # 시각화
                import matplotlib.pyplot as plt

                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(forecast_df['연도'], forecast_df['인구'], marker='o', linestyle='-')
                ax.set_title('Population Trend in Korea')
                ax.set_xlabel('Year')
                ax.set_ylabel('Population')

                # 예측점 강조
                ax.scatter([2035], [pred_2035], color='red', zorder=5)
                ax.text(2035, pred_2035, f'  Forecast: {pred_2035:,}', color='red', va='bottom')

                st.pyplot(fig)

                st.success(f"Forecasted population in 2035: {pred_2035:,}")
            else:
                st.info("Please upload population_trends.csv.")

        # 11. 지역별 인구 변화 분석
        with tabs[10]:
            st.header("📊 지역별 인구 변화 분석")

            # CSV 파일 업로드
            pop_file = st.file_uploader("population_trends.csv 파일 업로드", type="csv", key="region_pop_file")
            if pop_file:
                df_pop = pd.read_csv(pop_file)

                # 결측치 '-' 처리 및 숫자형 변환
                df_pop.replace("-", "0", inplace=True)
                df_pop['연도'] = pd.to_numeric(df_pop['연도'], errors='coerce')
                df_pop['인구'] = pd.to_numeric(df_pop['인구'], errors='coerce')
                df_pop = df_pop[df_pop['지역'] != '전국']  # 전국 제외
                df_pop.dropna(subset=['연도', '인구'], inplace=True)

                # 최근 5년 선택
                max_year = df_pop['연도'].max()
                min_year = max_year - 5
                recent_df = df_pop[df_pop['연도'].isin([min_year, max_year])]

                # 지역별로 피벗 테이블 생성 (5년 전, 현재 인구 비교)
                pivot = recent_df.pivot(index='지역', columns='연도', values='인구')
                pivot.dropna(inplace=True)

                # 변화량 (천 명 단위) 및 변화율 계산
                pivot['change'] = (pivot[max_year] - pivot[min_year]) / 1000
                pivot['rate'] = ((pivot[max_year] - pivot[min_year]) / pivot[min_year]) * 100

                # 지역명 한영 매핑
                kor_to_eng = {
                    '서울특별시': 'Seoul', '부산광역시': 'Busan', '대구광역시': 'Daegu',
                    '인천광역시': 'Incheon', '광주광역시': 'Gwangju', '대전광역시': 'Daejeon',
                    '울산광역시': 'Ulsan', '세종특별자치시': 'Sejong',
                    '경기도': 'Gyeonggi', '강원도': 'Gangwon',
                    '충청북도': 'Chungbuk', '충청남도': 'Chungnam',
                    '전라북도': 'Jeonbuk', '전라남도': 'Jeonnam',
                    '경상북도': 'Gyeongbuk', '경상남도': 'Gyeongnam',
                    '제주특별자치도': 'Jeju'
                }
                pivot['region_en'] = pivot.index.map(kor_to_eng)

                # 변화량 기준 내림차순 정렬
                pivot.sort_values('change', ascending=False, inplace=True)

                import seaborn as sns
                import matplotlib.pyplot as plt

                # --- 변화량 수평 막대 그래프 ---
                fig1, ax1 = plt.subplots(figsize=(10, 8))
                sns.barplot(
                    x='change', y='region_en',
                    data=pivot, ax=ax1, palette='coolwarm'
                )
                ax1.set_title("Population Change by Region (Last 5 Years)")  # 영어 제목
                ax1.set_xlabel("Population Change (thousands)")  # 영어 축
                ax1.set_ylabel("Region")

                # 각 막대에 수치 표시
                for i, (value, label) in enumerate(zip(pivot['change'], pivot['region_en'])):
                    ax1.text(value + 0.5 if value >= 0 else value - 2, i, f'{value:.1f}', va='center')

                st.pyplot(fig1)

                # --- 변화율 기준 수평 막대 그래프 ---
                pivot.sort_values('rate', ascending=False, inplace=True)
                fig2, ax2 = plt.subplots(figsize=(10, 8))
                sns.barplot(
                    x='rate', y='region_en',
                    data=pivot, ax=ax2, palette='viridis'
                )
                ax2.set_title("Population Change Rate by Region (Last 5 Years)")
                ax2.set_xlabel("Change Rate (%)")
                ax2.set_ylabel("Region")

                # 각 막대에 수치 표시
                for i, (value, label) in enumerate(zip(pivot['rate'], pivot['region_en'])):
                    ax2.text(value + 0.3 if value >= 0 else value - 2, i, f'{value:.1f}%', va='center')

                st.pyplot(fig2)

                # --- 해석 ---
                st.markdown("### 해석 (Interpretation)")
                st.markdown("""
                - 최근 5년간 인구가 증가한 지역은 수도권 및 개발 중인 도시 중심입니다.
                - 인구 감소 지역은 고령화, 출산율 저하, 청년층 유출 등이 원인일 수 있습니다.
                - 변화율(%)은 원래 인구가 적었던 지역에서 더 크게 나타날 수 있으며, 이는 상대적 성장성을 보여줍니다.
                """)
            else:
                st.info("population_trends.csv 파일을 업로드해주세요.")

        # 12. 지역별 인구 증감 상위 100
        with tabs[11]:
            st.header("📈 지역별 연도별 인구 증감 상위 100")

            pop_file = st.file_uploader("population_trends.csv 파일 업로드", type="csv", key="diff_pop_file")
            if pop_file:
                df_pop = pd.read_csv(pop_file)

                # 전처리
                df_pop.replace("-", "0", inplace=True)
                df_pop['연도'] = pd.to_numeric(df_pop['연도'], errors='coerce')
                df_pop['인구'] = pd.to_numeric(df_pop['인구'], errors='coerce')
                df_pop = df_pop[df_pop['지역'] != '전국']
                df_pop.dropna(subset=['연도', '인구'], inplace=True)

                # 연도 정렬
                df_pop.sort_values(['지역', '연도'], inplace=True)

                # 지역별 diff 계산
                df_pop['증감량'] = df_pop.groupby('지역')['인구'].diff()

                # 상위 100개 (절댓값 기준 내림차순)
                top_diff = df_pop.dropna(subset=['증감량']).copy()
                top_diff['증감량'] = top_diff['증감량'].astype(int)
                top_diff['증감량_천명'] = (top_diff['증감량'] / 1000).round(1)
                top_100 = top_diff.reindex(top_diff['증감량'].abs().sort_values(ascending=False).index).head(100)

                # 포맷팅 함수 정의
                def highlight_diff(val):
                    color = 'background-color: #fdd' if val < 0 else 'background-color: #ddf'
                    return color

                def format_thousands(x):
                    return f"{int(x):,}"

                styled_table = top_100[['지역', '연도', '증감량']].copy()
                styled_table['증감량'] = styled_table['증감량'].apply(format_thousands)

                st.subheader("📋 증감 기준 상위 100개 사례 (천 명 단위)")
                st.dataframe(
                    top_100[['지역', '연도', '증감량_천명']]
                    .style.background_gradient(
                        subset=['증감량_천명'],
                        cmap='RdBu_r',
                        vmin=-top_100['증감량_천명'].abs().max(),
                        vmax=top_100['증감량_천명'].abs().max()
                    )
                    .format({'증감량_천명': '{:,.1f}'})
                    .set_properties(**{'text-align': 'center'})
                )

                st.markdown("""
                - **파란색 배경**: 인구가 증가한 사례  
                - **빨간색 배경**: 인구가 감소한 사례  
                - 숫자는 천 명 단위로 표기되며, 정렬 기준은 증감 절댓값입니다.
                """)
            else:
                st.info("population_trends.csv 파일을 업로드해주세요.")

        # 13. 지역별 누적 인구 영역 그래프
        with tabs[12]:
            st.header("📊 Regional Stacked Area Chart of Population")

            pop_file = st.file_uploader("Upload population_trends.csv", type="csv", key="stacked_area_file")
            if pop_file:
                import pandas as pd
                import matplotlib.pyplot as plt
                import seaborn as sns

                df_pop = pd.read_csv(pop_file)

                # 전처리
                df_pop.replace("-", "0", inplace=True)
                df_pop['연도'] = pd.to_numeric(df_pop['연도'], errors='coerce')
                df_pop['인구'] = pd.to_numeric(df_pop['인구'], errors='coerce')
                df_pop = df_pop[df_pop['지역'] != '전국']
                df_pop.dropna(subset=['연도', '인구'], inplace=True)

                # 지역 한글 → 영어 맵핑
                kor_to_eng = {
                    '서울특별시': 'Seoul', '부산광역시': 'Busan', '대구광역시': 'Daegu',
                    '인천광역시': 'Incheon', '광주광역시': 'Gwangju', '대전광역시': 'Daejeon',
                    '울산광역시': 'Ulsan', '세종특별자치시': 'Sejong',
                    '경기도': 'Gyeonggi', '강원도': 'Gangwon',
                    '충청북도': 'Chungbuk', '충청남도': 'Chungnam',
                    '전라북도': 'Jeonbuk', '전라남도': 'Jeonnam',
                    '경상북도': 'Gyeongbuk', '경상남도': 'Gyeongnam',
                    '제주특별자치도': 'Jeju'
                }
                df_pop['region_en'] = df_pop['지역'].map(kor_to_eng)

                # 피벗 테이블 생성 (행: 연도, 열: 지역, 값: 인구)
                pivot_df = df_pop.pivot_table(index='연도', columns='region_en', values='인구', aggfunc='sum')
                pivot_df = pivot_df.fillna(0).astype(int)
                pivot_df.sort_index(inplace=True)

                # 누적 영역 그래프 그리기
                fig, ax = plt.subplots(figsize=(12, 6))
                pivot_df = pivot_df / 1000  # 단위: 천명
                pivot_df.plot.area(ax=ax, cmap='tab20')  # seaborn 스타일 색상 20종
                ax.set_title('Stacked Area Chart of Population by Region')
                ax.set_xlabel('Year')
                ax.set_ylabel('Population (thousands)')
                ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0), title="Region")
                plt.tight_layout()

                st.pyplot(fig)

                st.markdown("""
                - This stacked area chart shows population changes by region over the years.  
                - Each layer represents one region. The total height reflects cumulative population.  
                - Color distinctions make regional trends more visible.
                """)
            else:
                st.info("Please upload population_trends.csv.")

        # 14. population_trends.csv 전용 인구통계 EDA 탭
        with tabs[13]:
            st.header("📊 인구통계 EDA (population_trends.csv)")

            pop_file = st.file_uploader("population_trends.csv 파일 업로드", type="csv", key="pop_eda_file")
            if pop_file:
                df = pd.read_csv(pop_file)
                df.replace("-", "0", inplace=True)
                df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
                df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
                df['출생아수(명)'] = pd.to_numeric(df['출생아수(명)'], errors='coerce')
                df['사망자수(명)'] = pd.to_numeric(df['사망자수(명)'], errors='coerce')
                df.dropna(subset=['연도', '인구'], inplace=True)

                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"
                ])

                # 1. 기초 통계
                with tab1:
                    st.subheader("📋 기초 통계")
                    st.dataframe(df.describe())
                    import io
                    buffer = io.StringIO()
                    df.info(buf=buffer)
                    st.text(buffer.getvalue())

                # 2. 연도별 추이
                with tab2:
                    st.subheader("📈 전국 인구 연도별 추이")
                    nat = df[df['지역'] == '전국'].sort_values('연도')
                    fig, ax = plt.subplots()
                    ax.plot(nat['연도'], nat['인구'], marker='o')
                    ax.set_title("전국 인구 추이")
                    ax.set_xlabel("연도")
                    ax.set_ylabel("인구 수")
                    st.pyplot(fig)

                # 3. 지역별 분석
                with tab3:
                    st.subheader("📍 최신 연도 기준 지역별 인구")
                    latest = df['연도'].max()
                    latest_df = df[(df['연도'] == latest) & (df['지역'] != '전국')]
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.barplot(x='인구', y='지역', data=latest_df.sort_values('인구'), ax=ax)
                    ax.set_title(f"{latest}년 지역별 인구")
                    st.pyplot(fig)

                # 4. 변화량 분석
                with tab4:
                    st.subheader("🔄 연도별 인구 증감량 (Top 100)")
                    df_sorted = df[df['지역'] != '전국'].sort_values(['지역', '연도'])
                    df_sorted['증감량'] = df_sorted.groupby('지역')['인구'].diff()
                    top_diff = df_sorted.dropna(subset=['증감량']).copy()
                    top_diff['증감량'] = top_diff['증감량'].astype(int)
                    top_100 = top_diff.reindex(
                        top_diff['증감량'].abs().sort_values(ascending=False).index
                    ).head(100)

                    st.dataframe(top_100[['지역', '연도', '증감량']].style.background_gradient(
                        subset=['증감량'], cmap='coolwarm'))

                # 5. 시각화
                with tab5:
                    st.subheader("📊 지역별 누적 인구 영역 그래프")
                    pivot_df = df[df['지역'] != '전국'].pivot_table(
                        index='연도', columns='지역', values='인구', aggfunc='sum'
                    ).fillna(0)

                    fig, ax = plt.subplots(figsize=(12, 6))
                    (pivot_df / 1000).plot.area(ax=ax, cmap='tab20')
                    ax.set_title("지역별 누적 인구 변화 (천 명 단위)")
                    ax.set_ylabel("인구 (천 명)")
                    st.pyplot(fig)
            else:
                st.info("population_trends.csv 파일을 업로드해주세요.")

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login = st.Page(Login, title="Login", icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home",
                    default=True)
Page_User = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout = st.Page(Logout, title="Logout", icon="🔓", url_path="logout")
Page_EDA = st.Page(EDA, title="EDA", icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()