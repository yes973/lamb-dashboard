import streamlit as st
import pandas as pd
import math
from pathlib import Path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='GDP dashboard',
    page_icon=':earth_americas:', # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_gdp_data():
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    # The data above has columns like:
    # - Country Name
    # - Country Code
    # - [Stuff I don't care about]
    # - GDP for 1960
    # - GDP for 1961
    # - GDP for 1962
    # - ...
    # - GDP for 2022
    #
    # ...but I want this instead:
    # - Country Name
    # - Country Code
    # - Year
    # - GDP
    #
    # So let's pivot all those year-columns into two: Year and GDP
    gdp_df = raw_gdp_df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )

    # Convert years from string to integers
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

    return gdp_df

gdp_df = get_gdp_data()

# -----------------------------------------------------------------------------
# Sidebar navigation for multi-page layout
with st.sidebar:
    st.header('페이지 선택')
    selected_page = st.radio('', ['홈', '페이지 1', '페이지 2'], index=0)


def render_home_page():
    """Render the existing GDP dashboard page with its original tabs."""
    dashboard_tab, info_tab = st.tabs(["대시보드", "정보"])

    with dashboard_tab:
        '''
        # :earth_americas: GDP dashboard

        Browse GDP data from the [World Bank Open Data](https://data.worldbank.org/) website. As you'll
        notice, the data only goes to 2022 right now, and datapoints for certain years are often missing.
        But it's otherwise a great (and did I mention _free_?) source of data.
        '''

        ''
        ''

        min_value = gdp_df['Year'].min()
        max_value = gdp_df['Year'].max()

        from_year, to_year = st.slider(
            'Which years are you interested in?',
            min_value=min_value,
            max_value=max_value,
            value=[min_value, max_value])

        countries = gdp_df['Country Code'].unique()

        if not len(countries):
            st.warning("Select at least one country")

        selected_countries = st.multiselect(
            'Which countries would you like to view?',
            countries,
            ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

        ''
        ''
        ''

        # Filter the data
        filtered_gdp_df = gdp_df[
            (gdp_df['Country Code'].isin(selected_countries))
            & (gdp_df['Year'] <= to_year)
            & (from_year <= gdp_df['Year'])
        ]

        st.header('GDP over time', divider='gray')

        ''

        st.line_chart(
            filtered_gdp_df,
            x='Year',
            y='GDP',
            color='Country Code',
        )

        ''
        ''
        ''

        first_year = gdp_df[gdp_df['Year'] == from_year]
        last_year = gdp_df[gdp_df['Year'] == to_year]

        st.header(f'GDP in {to_year}', divider='gray')

        ''

        cols = st.columns(4)

        for i, country in enumerate(selected_countries):
            col = cols[i % len(cols)]

            with col:
                first_gdp = first_year[first_year['Country Code'] == country]['GDP'].iat[0] / 1000000000
                last_gdp = last_year[last_year['Country Code'] == country]['GDP'].iat[0] / 1000000000

                if math.isnan(first_gdp):
                    growth = 'n/a'
                    delta_color = 'off'
                else:
                    growth = f'{last_gdp / first_gdp:,.2f}x'
                    delta_color = 'normal'

                st.metric(
                    label=f'{country} GDP',
                    value=f'{last_gdp:,.0f}B',
                    delta=growth,
                    delta_color=delta_color
                )

    with info_tab:
        st.header('정보', divider='gray')
        st.write('이 탭에는 간단한 텍스트가 표시됩니다.')


def render_simple_page(page_title: str):
    """Render a simple page layout with top tabs and placeholder text."""
    tab1, tab2 = st.tabs(["탭 1", "탭 2"])
    with tab1:
        st.header(f'{page_title} - 탭 1', divider='gray')
        st.write(f'{page_title}의 간단한 텍스트입니다. 이 수정사항은 적용되었을까요?')
    with tab2:
        st.header(f'{page_title} - 탭 2', divider='gray')
        st.write(f'{page_title}의 간단한 텍스트입니다.')


# Route to the selected page
if selected_page == '홈':
    render_home_page()
elif selected_page == '페이지 1':
    render_simple_page('페이지 1')
elif selected_page == '페이지 2':
    render_simple_page('페이지 2')
