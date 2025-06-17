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
        st.title("📈 인구통계 EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)

        tabs = st.tabs([
            "기초 통계",
            "연도별 추이",
            "지역별 분석",
            "변화량 분석",
            "시각화",
        ])

        with tabs[0]:
            st.header("📊 Basic Statistics for Dataset")

            # 1. '세종'이 포함된 행 필터링
            sejong_df = df[df['지역'].str.contains('세종', na=False)].copy()

            # 2. '-' 를 0으로 치환
            sejong_df.replace("-", 0, inplace=True)

            # 3. 숫자형 변환 대상 열 정의 및 변환
            numeric_columns = ['인구', '출생아수(명)', '사망자수(명)']
            for col in numeric_columns:
                if col in sejong_df.columns:
                    sejong_df[col] = pd.to_numeric(sejong_df[col], errors='coerce').fillna(0)

            # 4. df.info() 출력
            st.subheader("1) 데이터프레임 구조 (`df.info()`)")
            buffer = io.StringIO()
            sejong_df.info(buf=buffer)
            st.text(buffer.getvalue())

            # 5. df.describe() 출력
            st.subheader("2) 요약 통계량 (`df.describe()`)")
            st.dataframe(sejong_df.describe())

            # 6. 데이터 미리보기
            st.subheader("3) 세종시 데이터 미리보기")
            st.dataframe(sejong_df.head())

        with tabs[1]:
            st.header("📈 National Population Trend and Forecast")

            # '-' 문자 0으로 처리
            df.replace("-", 0, inplace=True)

            # 숫자형 변환
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
            df['출생아수(명)'] = pd.to_numeric(df.get('출생아수(명)', 0), errors='coerce').fillna(0)
            df['사망자수(명)'] = pd.to_numeric(df.get('사망자수(명)', 0), errors='coerce').fillna(0)

            # 전국 데이터 필터링
            national_df = df[df['지역'] == '전국'].copy()
            national_df = national_df.sort_values(by='연도')

            # 최근 3년 평균 인구 증가 추정 (출생 - 사망)
            recent_df = national_df[national_df['연도'] >= national_df['연도'].max() - 2]
            recent_df['순증가'] = recent_df['출생아수(명)'] - recent_df['사망자수(명)']
            annual_increase = recent_df['순증가'].mean()

            # 2035년 인구 예측
            last_year = national_df['연도'].max()
            last_population = national_df[national_df['연도'] == last_year]['인구'].values[0]
            predicted_year = 2035
            predicted_population = last_population + annual_increase * (predicted_year - last_year)

            # 예측 포함 데이터프레임 구성
            extended_years = list(national_df['연도']) + [predicted_year]
            extended_populations = list(national_df['인구']) + [predicted_population]

            # 시각화
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(extended_years, extended_populations, marker='o', linestyle='-', color='blue', label='Population')
            ax.scatter(predicted_year, predicted_population, color='red', label='Prediction (2035)')
            ax.axvline(x=predicted_year, color='red', linestyle='--', linewidth=1)

            ax.set_title('National Population Forecast')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.legend()
            ax.grid(True)

            st.pyplot(fig)

            st.markdown(f"""
                - **Annual increase (avg birth - death, last 3 years)**: {annual_increase:,.0f}  
                - **Predicted population in 2035**: {predicted_population:,.0f}
            """)

        with tabs[2]:
            st.header("📊 Regional Population Change (Last 5 Years)")

            # 데이터 복사 및 전처리
            df.replace("-", 0, inplace=True)
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce')

            # '전국' 제외
            region_df = df[df['지역'] != '전국'].copy()

            # 가장 최근 연도 및 5년 전 기준 확인
            latest_year = region_df['연도'].max()
            base_year = latest_year - 5

            # 두 시점 데이터 분리
            df_latest = region_df[region_df['연도'] == latest_year][['지역', '인구']].rename(columns={'인구': '인구_최근'})
            df_base = region_df[region_df['연도'] == base_year][['지역', '인구']].rename(columns={'인구': '인구_5년전'})

            # 병합 후 변화량, 변화율 계산
            merged = pd.merge(df_latest, df_base, on='지역')
            merged['변화량'] = merged['인구_최근'] - merged['인구_5년전']
            merged['변화율'] = (merged['변화량'] / merged['인구_5년전']) * 100

            # 천 명 단위로 조정
            merged['변화량(천명)'] = merged['변화량'] / 1000

            # 지역명 영어로 번역 (간단 예시, 실제 번역 필요시 dict 확장 가능)
            translation = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            merged['Region'] = merged['지역'].map(translation).fillna(merged['지역'])

            # 변화량 그래프 (단위: 천 명)
            st.subheader("Change in Population (Last 5 Years)")
            fig1, ax1 = plt.subplots(figsize=(10, 8))
            sorted_df1 = merged.sort_values(by='변화량(천명)', ascending=False)
            sns.barplot(x='변화량(천명)', y='Region', data=sorted_df1, ax=ax1, palette='viridis')

            # 값 표시
            for i, val in enumerate(sorted_df1['변화량(천명)']):
                ax1.text(val + 1, i, f"{val:.1f}", va='center')

            ax1.set_xlabel("Change (Thousands)")
            ax1.set_ylabel("")
            ax1.set_title("Population Change by Region")
            st.pyplot(fig1)

            # 변화율 그래프
            st.subheader("Change Rate in Population (%)")
            fig2, ax2 = plt.subplots(figsize=(10, 8))
            sorted_df2 = merged.sort_values(by='변화율', ascending=False)
            sns.barplot(x='변화율', y='Region', data=sorted_df2, ax=ax2, palette='coolwarm')

            for i, val in enumerate(sorted_df2['변화율']):
                ax2.text(val + 0.2, i, f"{val:.1f}%", va='center')

            ax2.set_xlabel("Change Rate (%)")
            ax2.set_ylabel("")
            ax2.set_title("Population Growth Rate by Region")
            st.pyplot(fig2)

            # 해설
            st.markdown("""
                ### Interpretation
                - Regions at the top of the first chart have seen the highest increase in population over the last 5 years.
                - The second chart reveals which regions are growing the fastest in percentage terms.
                - Note that a region with a smaller population can show a high growth rate even with modest numeric increase.
                - Conversely, densely populated areas may have lower rates but larger numeric gains.
            """)

        with tabs[3]:
            st.header("📋 Population Changes by Region-Year")

            # 전처리
            df.replace("-", 0, inplace=True)
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
            region_df = df[df['지역'] != '전국'].copy()

            # 연도 기준 정렬 후 diff 계산
            region_df = region_df.sort_values(['지역', '연도'])
            region_df['증감'] = region_df.groupby('지역')['인구'].diff()

            # 증감 상위 100개 추출
            top_changes = region_df.dropna(subset=['증감']).copy()
            top_changes = top_changes.sort_values(by='증감', ascending=False, key=abs).head(100)

            # 숫자 포맷 (천단위 콤마)
            top_changes['인구'] = top_changes['인구'].map('{:,.0f}'.format)
            top_changes['증감'] = top_changes['증감'].map('{:,.0f}'.format)

            # 표 스타일링 함수 정의
            def highlight_change(val):
                val = val.replace(",", "")
                try:
                    val = float(val)
                    if val > 0:
                        color = '#cce5ff'  # 연파랑
                    elif val < 0:
                        color = '#ffcccc'  # 연빨강
                    else:
                        color = 'white'
                except:
                    color = 'white'
                return f'background-color: {color}'

            # 컬럼 선택 및 정리
            display_df = top_changes[['연도', '지역', '인구', '증감']].reset_index(drop=True)

            # 스타일링 및 출력
            styled_df = display_df.style.applymap(highlight_change, subset=['증감'])
            st.write(styled_df)

            st.markdown("""
                - **Top 100 population changes** across regions over all years.
                - Blue indicates increase, red indicates decrease.
                - Useful for spotting significant demographic shifts over short periods.
            """)

        with tabs[4]:
            st.header("📊 Stacked Area Plot of Regional Population Trends")

            # 전처리
            df.replace("-", 0, inplace=True)
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce')

            # '전국' 제외
            df_region = df[df['지역'] != '전국'].copy()

            # 지역명 영어 변환 (필요시 확장)
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            df_region['Region'] = df_region['지역'].map(region_map).fillna(df_region['지역'])

            # 피벗 테이블: 연도 x 지역
            pivot_df = df_region.pivot_table(index='연도', columns='Region', values='인구', aggfunc='sum')
            pivot_df = pivot_df.sort_index()

            # 누적 영역 그래프 생성
            fig, ax = plt.subplots(figsize=(12, 6))

            # 누적 영역
            colors = sns.color_palette("tab20", n_colors=pivot_df.shape[1])
            pivot_df.fillna(0).plot.area(ax=ax, stacked=True, color=colors)

            ax.set_title("Regional Population Stacked Area Chart")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(loc='center left', bbox_to_anchor=(1.0, 0.5), title="Region")
            ax.grid(True)

            st.pyplot(fig)

            st.markdown("""
                ### Interpretation
                - This area chart displays how each region contributes to the total population over time.
                - You can observe the **growth or decline trends** of individual regions clearly due to stacking.
                - The use of distinctive colors ensures each region is easily identifiable.
            """)



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