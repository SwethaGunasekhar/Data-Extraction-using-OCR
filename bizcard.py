import pandas as pd
import numpy as np
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import re
import io
# creating database
import mysql.connector
connection=mysql.connector.connect(       
    host='localhost',
    user='root',
    password='12345678',
    database='BizCard_Project')
cursor=connection.cursor()

def img_to_text(path):
    img=Image.open(path)
    img_array=np.array(img)
    reader=easyocr.Reader(['en'])
    text=reader.readtext(img_array,detail=0)
    return text,img

def extracted_text(text):
    extracted_dict={"Name":[],"Designation":[],"Company_Name":[],"Contact":[],"Email":[],"Website":[],"Address":[],"Pincode":[]}
    extracted_dict["Name"].append(text[0])
    extracted_dict["Designation"].append(text[1])
    for i in range(2, len(text)):
        if text[i].startswith("+") or text[i].replace("-","").isdigit() and '-' in text[i]:
            extracted_dict["Contact"].append(text[i])
        elif "@" in text[i] and ".com" in text[i]:
            extracted_dict["Email"].append(text[i])
        elif "WWW" in text[i] or "www" in text[i] or "Www" in text[i] or "wWw" in text[i] or "wwW" in text[i] :
            lower_text=text[i].lower()
            extracted_dict["Website"].append(lower_text)
        elif "TamilNadu" in text[i] or "Tamil Nadu" in text[i] or text[i].isdigit():
            extracted_dict["Pincode"].append(text[i])
        elif re.match(r'^[a-zA-Z]',text[i]):
            extracted_dict["Company_Name"].append(text[i])
        else:
            remove=re.sub(r'[,;]','',text[i])
            extracted_dict["Address"].append(remove)

    for key,value in extracted_dict.items():
        if len(value)>0:
            concatenate=" ".join(value)
            extracted_dict[key]=[concatenate]

        else:
            value="NA"
            extracted_dict[key]=[value]
            
    return extracted_dict   


#Streamlit part
st.set_page_config(layout="wide")
st.title("BizCardX: Extracting Business Card Data with OCR")
with st.sidebar:
    select=option_menu("Menu",["Home","Upload & Modify","Delete"])
if select=="Home":
    st.markdown(":blue[*BizCard application is used for extracting the information from the business cards. It helps in collecting the necessary information using different technologies and stores in database thereby reducing time & efforts spent on manual data entry.*]")
    st.subheader(":rainbow[*Technologies Used in Data Extraction*]")
    st.write(":green[1.*Python*]")
    st.write(":green[2.*EasyOCR*]")
    st.write(":green[3.*Pandas*]")
    st.write(":green[4.*Streamlit*]")
    st.write(":green[5.*SQL*]")
elif select=="Upload & Modify":
    img=st.file_uploader("Upload the image", type=["png","jpg","jpeg"])
    if img is not None:
        st.image(img,width=300)
        text_image,input_img=img_to_text(img)
        text_dict=extracted_text(text_image)
        if text_dict:
            st.success("Text is extracted successfully")
        df=pd.DataFrame(text_dict)
        #converting image to bytes
        img_bytes=io.BytesIO()
        input_img.save(img_bytes,format="PNG")
        img_data=img_bytes.getvalue()
        data={"IMAGE":[img_data]}
        df1=pd.DataFrame(data)
        concat_df=pd.concat([df,df1],axis=1)
        st.dataframe(concat_df)

        button1=st.button("Save")
        if button1:
            #SQL table creation
            Create_table= '''Create TABLE IF NOT EXISTS Bizcard_Info(Name varchar(255),
                                                                      Designation varchar(255),
                                                                      Company_Name varchar(255),
                                                                      Contact varchar(255),
                                                                      Email varchar(255),
                                                                      Website text,
                                                                      Address text,
                                                                      Pincode varchar(255),
                                                                      Image LONGBLOB
                                                                      )'''
            cursor.execute(Create_table)
            # insert values to columns
            insert_query = '''INSERT INTO Bizcard_Info(Name,Designation,Company_Name,Contact,Email,Website,Address,Pincode,Image)
                           values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            data= concat_df.values.tolist()[0]
            cursor.execute(insert_query,data)
            connection.commit()
            st.success("Details saved successfully")
        
        method=st.radio("Select the method",["Preview","Modify"])
        if method=="Preview":
            #Creating dataframe
            Query2= "Select * from Bizcard_Info"
            cursor.execute(Query2)
            Table=cursor.fetchall()
            df=pd.DataFrame(Table,columns=("Name","Designation","Company_Name","Contact","Email","Website","Address","Pincode","Image"))
            st.dataframe(df)

       
        elif method=="Modify":
            Query2= "Select * from Bizcard_Info"
            cursor.execute(Query2)
            Table=cursor.fetchall()
            df=pd.DataFrame(Table,columns=("Name","Designation","Company_Name","Contact","Email","Website","Address","Pincode","Image"))
            col1,col2= st.columns(2)
            with col1:
                Selected_name= st.selectbox("Select the name",df["Name"])
            df_1= df[df["Name"]==Selected_name]
            st.dataframe(df_1)
            df_2= df_1.copy()
            col1,col2=st.columns(2)
            with col1:
                m_name=st.text_input("Name",df_1["Name"].unique()[0])
                m_designation=st.text_input("Designation",df_1["Designation"].unique()[0])
                m_Companyname=st.text_input("Company_Name",df_1["Company_Name"].unique()[0])
                m_Contact=st.text_input("Contact",df_1["Contact"].unique()[0])
                m_Email=st.text_input("Email",df_1["Email"].unique()[0])
                df_2["Name"]=m_name
                df_2["Designation"]=m_designation
                df_2["Company_Name"]=m_Companyname
                df_2["Contact"]=m_Contact
                df_2["Email"]=m_Email
            with col2:
                m_Website=st.text_input("Website",df_1["Website"].unique()[0])
                m_Address=st.text_input("Address",df_1["Address"].unique()[0])
                m_Pincode=st.text_input("Pincode",df_1["Pincode"].unique()[0])
                m_Image=st.text_input("Image",df_1["Image"].unique()[0])
                df_2["Website"]=m_Website
                df_2["Address"]=m_Address
                df_2["Pincode"]=m_Pincode
                df_2["Image"]=m_Image
            st.dataframe(df_2)
            col1,col2=st.columns(2)
            with col1:
                button2=st.button("Modify")
                if button2:
                    cursor.execute(f"DELETE FROM Bizcard_Info WHERE NAME='{Selected_name}'")
                    connection.commit()
                    insert_query = '''INSERT INTO Bizcard_Info(Name,Designation,Company_Name,Contact,Email,Website,Address,Pincode,Image)
                               values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                    data= df_2.values.tolist()[0]
                    cursor.execute(insert_query,data)
                    connection.commit()
                    st.success("Modified data successfully")
            
               
elif select=="Delete":
    col1,col2=st.columns(2)
    with col1:
        select_query="Select Name from Bizcard_Info"
        cursor.execute(select_query)
        table1=cursor.fetchall()
        names=[]
        for i in table1:
            names.append(i[0])
        name_select=st.selectbox("Select the name",names)
        
    with col2:
        select_query=f"Select Designation from Bizcard_Info WHERE Name = '{name_select}'"
        cursor.execute(select_query)
        table2=cursor.fetchall()
        designations=[]
        for j in table2:
            designations.append(j[0])
        designation_select=st.selectbox("Select the designation",designations)

    if name_select and designation_select:
        col1,col2=st.columns(2)

        with col1:
            st.write(f"Selected Name: {name_select}")
            st.write(f"Selected Designation: {designation_select}")

        with col2:
            st.write("")
            st.write("")
            st.write("")
            remove=st.button("Delete")
            if remove:
                cursor.execute(f"Delete from Bizcard_Info where Name='{name_select}' and Designation='{designation_select}'")
                connection.commit()
                st.warning("DELETED")