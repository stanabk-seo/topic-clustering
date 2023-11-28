import streamlit as st
import pandas as pd
import requests
import json
import csv
import ast
from itertools import combinations
from collections import Counter
import time
import math
import streamlit_ext as ste
from serpapi import GoogleSearch
from datetime import datetime

st.header('Keyword Clustering by SERP Similarity', divider='rainbow')

st.subheader("Upload a CSV (UTF-8) file with Keywords and Search Volume.")
st.link_button("Download Sample File", "https://drive.google.com/uc?export=download&id=1guDxWCz1gYev6cq4JYHY_KTyjPHBneiN")

@st.cache_data
def load_data(file):
    df = pd.read_csv(file, encoding='utf-8')
    return df

uploaded_file = st.file_uploader('Upload CSV File', type='csv')


col3, col4 = st.columns(2)

with col3:
    serp_api_key = None
    serp_api_key = st.text_input('**Enter Your SERP API Key:**')
with col4:
    location = st.selectbox("**Choose Country:**",("Choose Country","United States", "India", "United Kingdom","Australia","Canada"), placeholder='Choose Country')

if uploaded_file is None:
    st.write('')
elif not serp_api_key:
    st.write("Please enter SERP API Key")
elif location == "Choose Country":
    st.write("Please Select Country")
else:
    #main_code_starts_here

    data = load_data(uploaded_file)
    # data = pd.read_csv(file, encoding='utf-8')
    no_of_keywords = len(data['keywords'])
    st.markdown('**Your Data:**')
    st.caption('You have uploaded ' + str(no_of_keywords) + ' keywords.')
    current_time = datetime.now().time()
    st.caption(current_time)
    st.write(data)
    # data = pd.read_csv(r'~/Desktop/python_scripts/similarity_checker/keywords.csv', encoding='latin-1')
    queries = data['keywords'].tolist()
    search_volume = data['search_volume'].tolist()
    # print(queries)

    #serp_scraping
    all_data = []



    my_bar = st.progress(0)

    for (i,j,k) in zip(queries,search_volume,range(no_of_keywords)):
        params = {
        "api_key": serp_api_key,
        "q": i,
        "location": location,
        "engine": "google",
        'gl': 'us',
        'google_domain': 'google.com',
        'hl': 'en'
        }

        print('Scraping Started')
        progress_text = 'Scraping SERP. Please wait. ' + str(round(((k+1)/no_of_keywords)*100)) + '% Completed. Current keyword: ' + str(i)
        my_bar.progress(int(((k+1)/no_of_keywords)*100), text=progress_text)
        print(progress_text)


        try:
            #serp_api
            search = GoogleSearch(params)
            json_results = search.get_dict()
            query = json_results["search_parameters"]['q']
            volume = j
        
        except:
            #value_serp
            search = requests.get('https://api.valueserp.com/search', params)
            results = json.dumps(search.json(), indent=4)
            json_results = json.loads(results)
            query = json_results["search_parameters"]['q']
            volume = j

        try:
            featured_snippet = json_results["answer_box"]["answers"][0]["source"]["link"]
            all_data.append((query,featured_snippet,volume))
        except:
            try:
                featured_snippet = json_results["answer_box"]["link"]
                all_data.append((query,featured_snippet,volume))
            except:
                all_data.append((query, 'no_featured_snippet', volume))

        for i in range(0,10):
            try:
                link = json_results["organic_results"][i]["link"]
                link = link.replace("'", "")
                all_data.append((query, link, volume))
            except:
                all_data.append((query, 'no_data', volume))

    # print(organic_link)
    # print(keyword)
    my_bar.empty()

    #creating_data_to_cluster
    all_data_df = pd.DataFrame(all_data)
    all_data_df.columns = ['topic','links','search_volume']
    all_data_df = all_data_df[all_data_df.links != 'no_featured_snippet']
    all_data_df = all_data_df[all_data_df.links != 'no_data']
    # print(all_data_df)

    #transposing_links
    df = pd.DataFrame(all_data_df.groupby(['topic','search_volume'])['links'].apply(lambda df: df.reset_index(drop=True)).unstack()).reset_index()

    #concatenating_all_links_in_one_column

    df['serp_data'] = df.apply(lambda row: f"[\'{row[0]}', '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}', '{row[5]}','{row[6]}', '{row[7]}', '{row[8]}', '{row[9]}\']", axis=1)

    final_df = df[['topic','serp_data','search_volume']]
    # final_df.fillna('No Data')
    st.subheader('SERP Data')
    st.dataframe(final_df.head(100))
    #csv = final_df.to_csv().encode('utf-8')
    # ste.download_button(label='Download SERP Data', data=csv,file_name='serp_data.csv',mime='text/csv')
    # print(final_df)

    # topic_clustering

    # final_df = pd.read_csv(r'~/Desktop/python_scripts/similarity_checker/serp_output_merged.csv' ,encoding='latin-1')
    # print(final_df)
    search_volume_df = final_df[['topic','search_volume']]

    keyword_list = final_df['topic'].tolist()
    url_list = final_df['serp_data'].tolist()

    keyword_1 = []
    keyword_2 = []
    results = []
    filtered_results = []

    my_bar = st.progress(0)
    kw_count = math.comb(len(keyword_list),2)


    for (keyword_a, keyword_b), (list_1, list_2), i in zip(combinations(keyword_list, 2), combinations(url_list, 2), range(kw_count)):
        progress_text = 'Clustering Topics. Please wait. Progress: ' + str(round(int(((i+1)/kw_count)*100))) + "%"
        my_bar.progress(int(((i+1)/kw_count)*100), text=progress_text)
        print(progress_text)
        list_a = ast.literal_eval(list_1)
        list_b = ast.literal_eval(list_2)
        same_domains = set(list_a).intersection(list_b)
        length = len(same_domains)
        keyword_1.append(keyword_a)
        keyword_2.append(keyword_b)
        results.append((keyword_a, keyword_b, list_1, list_2, length))
        if length >= 3:
            filtered_results.append((keyword_a, keyword_b, list_1, list_2, length))

        
    my_bar.empty()

    #creating_common_urls_df
    output_df = pd.DataFrame(results, columns=['topic_a', 'topic_b', 'links_a','links_b','common_urls'])
    output_df_2 = output_df.merge(search_volume_df, left_on='topic_a', right_on='topic', how='left')
    output_df_2 = output_df_2.drop(columns='topic').rename(columns={'search_volume': 'search_volume_a'})
    output_df_3 = output_df_2.merge(search_volume_df, left_on='topic_b', right_on='topic', how='left')
    output_df_4 = output_df_3.drop(columns='topic').rename(columns={'search_volume': 'search_volume_b'})
    # print(output_df_4)

    #creating_cluster_df

    filtered_output_df = pd.DataFrame(filtered_results, columns=['topic_a', 'topic_b', 'links_a','links_b','common_urls'])

    final_df_2 = filtered_output_df.merge(search_volume_df, left_on='topic_a', right_on='topic', how='left')
    final_df_2 = final_df_2.drop(columns='topic').rename(columns={'search_volume': 'search_volume_a'})
    final_df_3 = final_df_2.merge(search_volume_df, left_on='topic_b', right_on='topic', how='left')
    final_df_4 = final_df_3.drop(columns='topic').rename(columns={'search_volume': 'search_volume_b'})
    # print(final_df_4)

    st.subheader('Topic Clusters')
    st.write(final_df_4.head(100))
    csv = final_df_4.to_csv().encode('utf-8')
    ste.download_button(label='Download Topic Clusters', data=csv,file_name='topic_clusters.csv',mime='text/csv')

    #final_df_4.to_csv('~/Desktop/python_scripts/similarity_checker/cluster_output.csv')

    # preparing_df_for_treemap

    cluster_df = final_df_4.groupby('topic_a').agg(related_topics=('topic_b',list), kw_count = ('topic_b','count'), related_kws_volume=('search_volume_b','sum')).reset_index()
    cluster_df_2 = cluster_df.merge(search_volume_df, left_on='topic_a', right_on='topic', how='left')
    cluster_df_2 = cluster_df_2.drop(columns='topic')
    cluster_df_2['total_volume'] = cluster_df_2['related_kws_volume'] + cluster_df_2['search_volume']
    cluster_df_3 = cluster_df_2.drop(columns=['related_kws_volume','search_volume']).rename(columns={'topic_a': 'cluster'}).sort_values(by='total_volume', ascending=False).reset_index(drop=True)
    cluster_df_4 = cluster_df_3.explode('related_topics')
    cluster_df_4 = cluster_df_4.merge(search_volume_df, left_on='related_topics',right_on ='topic', how='left')
    cluster_df_4 = cluster_df_4.drop(columns='topic').rename(columns={'search_volume': 'related_topics_search_volume'})


    # cluster_df_3.to_csv(r'~/Desktop/python_scripts/similarity_checker/serp_similarity_output.csv')

    #plotting_graph

    cluster_df_4 = cluster_df_4[cluster_df_4['related_topics_search_volume'] != 0]
    # print(cluster_df_4)

    import plotly.express as px
    import plotly.graph_objects as go

    fig = px.treemap(cluster_df_4, 
                    path=[px.Constant("Topic Clusters"), 'cluster','related_topics'], 
                    values='total_volume',
                    color='total_volume', 
                    color_continuous_scale='RdBu',
                    custom_data=[cluster_df_4['total_volume'], cluster_df_4['kw_count'], cluster_df_4['related_topics_search_volume']],
                    # labels={'cluster': 'total_volume','related_topics':'kw_count'}
                    # labels={'customdata': 'Keyword Count: '}
    )

    # Update hover template to display custom data
    fig.update_traces(
        hovertemplate="Total Cluster Volume: %{customdata[0]}<br>Keyword Count: %{customdata[1]}<br>Keyword Volume: %{customdata[2]}"
    )

    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    # fig.update_traces(hovertemplate=None)
    st.subheader('Topic Cluster Graph')
    st.plotly_chart(fig, use_container_width=True)

st.write("made by: abhishek.shukla")
st.write("Facing issues?")
href2 = f'<a href="https://www.linkedin.com/in/abhishekshukla01/">DM me on Linkedin</a>'
href3 = f'<a href="https://twitter.com/StanAbK">DM me on Twitter</a>'
st.markdown(href2, unsafe_allow_html=True)
st.markdown(href3, unsafe_allow_html=True)
