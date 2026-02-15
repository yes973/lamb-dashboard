import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
import json

# 1. 페이지 설정
st.set_page_config(page_title="동물병원 경영 벤치마크", layout="wide")

# 2. Firebase 초기화 함수 (비밀키 관리 중요!)
# Streamlit Cloud에 배포할 때는 'Secrets' 기능을 사용하고,
# 로컬에서 테스트할 때는 json 파일을 직접 로드합니다.
@st.cache_resource
def init_firebase():
    # 이미 앱이 초기화되었는지 확인 (중복 초기화 방지)
    if not firebase_admin._apps:
        # 실전 배포시: st.secrets에서 정보 로드
        if 'firebase_key' in st.secrets:
            key_dict = json.loads(st.secrets['firebase_key'])
            cred = credentials.Certificate(key_dict)
        # 로컬 테스트시: 다운받은 json 파일 경로 입력
        else:
            cred = credentials.Certificate("serviceAccountKey.json_경로를_여기에_입력하세요")
        
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

# 3. 데이터 로드
@st.cache_data
def load_data():
    # 1단계에서 만든 csv 파일
    return pd.read_csv('hospital_stats_processed.csv')

df = load_data()

# --- UI 구성 ---
st.title("📊 국내 동물병원 경영 벤치마크 서비스")
st.markdown("나의 병원 매출을 입력하고, 동종 업계 내 위치를 확인해보세요.")

with st.sidebar:
    st.header("입력 설정")
    selected_year = st.selectbox("조사 연도", df['조사기준연도'].unique())
    selected_region = st.selectbox("지역", df['행정구역코드'].unique())
    
    st.divider()
    
    # 사용자 입력
    my_revenue = st.number_input(
        "우리 병원 연 매출 (단위: 만원)", 
        min_value=0, 
        value=50000, 
        step=1000
    )
    
    check_btn = st.button("내 위치 확인하기 & 데이터 저장")

# --- 메인 분석 로직 ---

# 선택한 조건에 맞는 통계 데이터 필터링
target_stat = df[
    (df['조사기준연도'] == selected_year) & 
    (df['행정구역코드'] == selected_region)
]

if not target_stat.empty:
    stat = target_stat.iloc[0]
    
    # 시각화 (Plotly 사용)
    fig = go.Figure()

    # 배경: 업계 분포 (Box Plot 형태의 Bar)
    fig.add_trace(go.Bar(
        x=['업계 분포'],
        y=[stat['상위10%'] - stat['하위25%']],
        base=stat['하위25%'],
        marker_color='lightgray',
        name='중위 50% 구간',
        opacity=0.5
    ))
    
    # 평균선
    fig.add_trace(go.Scatter(
        x=['업계 분포'], y=[stat['평균매출']],
        mode='markers+text',
        marker=dict(color='blue', size=15, symbol='line-ew-open'),
        name=f"지역 평균 ({int(stat['평균매출']):,}만원)",
        text=[f"평균"], textposition="middle left"
    ))

    # 내 병원 위치
    fig.add_trace(go.Scatter(
        x=['업계 분포'], y=[my_revenue],
        mode='markers+text',
        marker=dict(color='red', size=20, symbol='diamond'),
        name=f"우리 병원 ({my_revenue:,}만원)",
        text=["ME"], textposition="middle right"
    ))

    fig.update_layout(
        title=f"{selected_year}년 {selected_region} 매출 분석",
        yaxis_title="매출 (만원)",
        showlegend=True,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 텍스트 분석 결과
    if my_revenue >= stat['상위25%']:
        st.success(f"축하합니다! 상위 25% ({int(stat['상위25%']):,}만원) 이상인 고매출 병원입니다.")
    elif my_revenue <= stat['하위25%']:
        st.warning("매출 증대 전략이 필요해 보입니다. 하위 25% 구간에 위치합니다.")
    else:
        st.info("안정적인 운영 중입니다. 평균 범위 내에 위치합니다.")

# --- 4. Firebase 데이터 저장 (로그 수집) ---
if check_btn:
    try:
        db = init_firebase()
        
        # 저장할 데이터 (익명성 유지)
        log_data = {
            "timestamp": datetime.now(),
            "year": int(selected_year),
            "region": selected_region,
            "input_revenue": int(my_revenue),
            # 원한다면 여기서 ip 정보 등을 추가 수집 가능 (st.query_params 등 활용)
        }
        
        # 'user_logs'라는 컬렉션(폴더)에 문서 추가
        db.collection("user_logs").add(log_data)
        
        st.toast("✅ 데이터 분석이 완료되었습니다. (로그 저장됨)", icon="💾")
        
    except Exception as e:
        # 로컬 테스트시 키 파일 경로가 틀리면 에러 날 수 있음
        st.error(f"로그 저장 중 오류 발생: {e}")
