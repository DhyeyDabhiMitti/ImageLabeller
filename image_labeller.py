import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from PIL import Image
import boto3
import os
import io
from ast import literal_eval

def save_df(input_df):
    with io.StringIO() as csv_buffer:
        input_df.to_csv(csv_buffer, index=False)
        response = st.session_state.s3.put_object(
            Bucket=st.session_state.bucket_name, Key="Mitti-Data/Field_Inspection_Annotated_Test.csv", Body=csv_buffer.getvalue()
        )
        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")\
    
    return status

def add_user(user_name):
    st.session_state.data[user_name] = None
    save_df(st.session_state.data)
    st.session_state.users.append(user_name)
    return None

def safe_literal_eval(input_str):
    try:
        return literal_eval(input_str)
    except:
        return None


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


## Initiate the df ##
if 'data' not in st.session_state:
    response = st.session_state.s3.get_object(Bucket=st.session_state.bucket_name, Key="Mitti-Data/Field_Inspection_Annotated_Test.csv")
    st.session_state['data'] = pd.read_csv(response.get("Body"))
    st.session_state['data']['FieldPhot1hldr'].fillna('None')
    st.session_state['data']['FieldPhot2hldr'].fillna('None')
df = st.session_state['data']

## Initiate users ##
if 'users' not in st.session_state:
    st.session_state['users'] = df.columns[17:]
users = st.session_state['users']

## get the user and initiate the counter name as well as the counter ##
user = st.selectbox('Who is annotating?',users)
st.session_state['current_user'] = user
new_user = st.checkbox('Add User')
if new_user:
    with st.form(key='new_user_form'):
        user_name = st.text_input('Enter your name:')
        submit_button = st.form_submit_button("Submit")
        if submit_button:
            add_user(user_name)
            st.rerun()

counter_name = st.session_state['current_user']+'_counter'

if counter_name not in st.session_state:
    st.session_state[counter_name] = df[user].count()

## initiate the index and check the stopping condition ##
index = st.session_state[counter_name]
if index>=df.shape[0]:
    st.write("You have annotated all the images!")
    st.stop()
st.write('Currently Processed ',index,' Images!!')

field = str(df.loc[index,'croppableAreaId'])
date = str(df.loc[index,'executedOn'])

st.write("Images are for the field: ",df.loc[index,'croppableAreaId'])
st.write("Field Inspection Details: ")
st.write("Plant Height: ",df.loc[index,'PlantHeig3'])
st.write("Water Height: ",df.loc[index,'WaterHeig0'])
if df.loc[index,'FieldPhot1hldr']!='None':
    fail_counter = 0
    try_counter = 0
    key = 'CropIn_Photos/'+str(df.loc[index,'FieldPhot1hldr'])
    try:
        try_counter+=1
        response = st.session_state['s3'].get_object(Bucket=st.session_state['bucket_name'], Key=key)
        image_content = response['Body'].read()
        image = Image.open(io.BytesIO(image_content))
        st.image(image)
    except:
        fail_counter+=1
if df.loc[index,'FieldPhot2hldr']!='None':
    try:
        try_counter+=1
        key = 'CropIn_Photos/'+df.loc[index,'FieldPhot2hldr']
        response = st.session_state['s3'].get_object(Bucket=st.session_state['bucket_name'], Key=key)
        image_content = response['Body'].read()
        image = Image.open(io.BytesIO(image_content))
        st.image(image)
    except:
        fail_counter+=1



if df.loc[index,'Soilmoist5hldr']!=None:
    st.write(type(df.loc[index,'Soilmoist5hldr']))
    lst = safe_literal_eval(df.loc[index,'Soilmoist5hldr'])
    st.write(lst)
    for image in lst:
        try:
            try_counter+=1
            key = 'CropIn_Photos/'+image['originalFileName']
            response = st.session_state['s3'].get_object(Bucket=st.session_state['bucket_name'], Key=key)
            image_content = response['Body'].read()
            image = Image.open(io.BytesIO(image_content))
            st.image(image)
        except:
            fail_counter+=1

if fail_counter==try_counter:
    df.loc[st.session_state[st.session_state['current_user']+'_counter'],st.session_state['current_user']] = -1
    status = save_df(df)
    if status==200:
        st.write("Successful!!")
    st.session_state[st.session_state['current_user']+'_counter']+=1
    st.session_state['data']=df
    st.rerun()
    
with st.form(key='my_form'):
        input_text = st.selectbox("Is Field Inundated?",['inundated','non-inundated','not sure'])
        if input_text == 'inundated':
            label = 1
        if input_text == 'non-inundated':
            label = 0
        if input_text == 'not sure':
            label = 0.5
        st.session_state.label=label
        submit_button = st.form_submit_button("Submit")
        if submit_button:
                try:
                    label = int(st.session_state.label)
                    df.loc[st.session_state[st.session_state['current_user']+'_counter'],st.session_state['current_user']] = label
                    status = save_df(df)
                    if status==200:
                        st.write("Successful!!")
                    st.session_state[st.session_state['current_user']+'_counter']+=1
                    st.session_state['data']=df
                except:
                    st.write('Enter an integer value!!!')
                st.rerun()


