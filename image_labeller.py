import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from PIL import Image
import boto3
import os

def update_index():
    try:
        label = int(st.session_state.label)
        df.loc[st.session_state['counter'],st.session_state['current_user']] = label
        df.to_csv('./data/Field_Inspection_Field_Photos.csv',index=False)
        st.session_state[st.session_state['current_user']+'_counter']+=1
        st.write(st.session_state[st.session_state['current_user']+'_counter'])
        st.session_state['data']=df
    except:
        st.write('Enter an integer value!!!')


st.title('Image Labelling Dashboard!')

## Initiate s3 session ##
if 's3' not in st.session_state:
    id = st.secrets['aws_access_key_id']
    access_key = st.secrets['aws_secret_access_key']
    region_name = st.secrets['region_name']
    st.session_state['bucket_name'] = st.secrets['bucket_name']
    s3 = boto3.client('s3', aws_access_key_id=id,
                  aws_secret_access_key=access_key,
                  region_name=region_name)
    st.session_state['s3'] = s3

print('S3 session initiated!')


## Initiate users ##
if 'users' not in st.session_state:
    st.session_state['users'] = ('Dhyey','Akshay','Raja','Shivang','Nate')

users = st.session_state['users']

if 'data' not in st.session_state:
    st.session_state['data'] = pd.read_csv('./data/Field_Inspection_Field_Photos.csv')
    for temp_user in users:
        st.session_state['data'][temp_user] = None
    st.session_state['data']['FieldPhot1hldr'].fillna('None')
    st.session_state['data']['FieldPhot2hldr'].fillna('None')
df = st.session_state['data']

print('Data added to the session state!')

user = st.selectbox('Who is annotating?',users)
st.session_state['current_user'] = user
counter_name = st.session_state['current_user']+'_counter'

if counter_name not in st.session_state:
    st.session_state[counter_name] = df[user].count()

print('Counter initiated!')
index = st.session_state[counter_name]
st.write('Currently Processed ',index,' Images!!')

field = str(df.loc[index,'croppableAreaId'])
date = str(df.loc[index,'executedOn'])
print(index)
print('Local variables initiated!')

if df.loc[index,'FieldPhot1hldr']!='None':
    print('Starting Image 1 processing!')
    key = 'CropIn_Photos/'+str(df.loc[index,'FieldPhot1hldr'])
    try:
        response = st.session_state['s3'].get_object(Bucket=st.session_state['bucket_name'], Key=key)
        image_content = response['Body'].read()
        image = Image.open(io.BytesIO(image_content))
        st.image(image)
    except:
        pass
if df.loc[index,'FieldPhot2hldr']!='None':
    print('Starting Image 2 processing!')
    try:
        key = 'CropIn_Photos/'+df.loc[index,'FieldPhot2hldr']
        response = st.session_state['s3'].get_object(Bucket=st.session_state['bucket_name'], Key=key)
        image_content = response['Body'].read()
        image = Image.open(io.BytesIO(image_content))
        st.image(image)
    except:
        pass


with st.form(key='my_form'):
        input_text = st.text_input("Is Field Inundated?",key='label',value="0:not-inundated & 1:inundated")
        st.write(st.session_state.label)
        submit_button = st.form_submit_button("Submit",on_click=update_index)


