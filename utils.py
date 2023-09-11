import os
import pytz
import json
import logging
from nectaapi import student,summary,comparison
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import pymongo
from urllib.parse import quote_plus

Mongo_client = pymongo.MongoClient(os.getenv("MONGODB_URI"))

MY_DB=Mongo_client["NectaAPI"]
performance_collection=MY_DB["Performance"]



# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def structure_student_results_message(data):
  year=data.get("matokeo_year")
  exam_type= "csee" if data.get("matokeo_exam_type")== '1' else "acsee"
  school_number=(data.get("matokeo_school_number"))
  student_number=(data.get("matokeo_student_number"))
  
  try:
    
    results = student.student(year, exam_type, school_number, student_number)
    
    if results:
      subjects=[f"{sub} >> {score}" for sub,score in results.get("subjects").items()]
      
      message=f"""Matokeo:\nschool name:{results.get('school_name')}\ngender:{results.get('gender')}\nDivision:{results.get('division')}\nPoints:{results.get('points')}\nsubjects score: {subjects}
      """
      return message

  except Exception as error:
    logging.error(f"{error} while structuring student results summary")
    return "Samahani sijaweza kupata matokeo yako"



# comparison.schoolPresent(year, exam_type, school_number)

async def school_summary(data:dict,messenger):
  year=data.get("ufaulu_wa_shule_year")
  exam_type= "csee" if data.get("ufaulu_wa_shule_exam_type")== '1' else "acsee"
  school_number=(data.get("ufaulu_wa_shule_school_number"))
  image_name=f"{year}_{exam_type}_{str(school_number).upper()}.png"
  
  if os.path.exists(os.path.join("./Imgs/Performance",image_name)):
    print("here")
    return get_saved_details(image_name,messenger)
  
  try:
    # check if the school participated in exams in particular year
    Is_present=comparison.schoolPresent(year, exam_type, school_number)
    
    if Is_present:
      # find results summary
      data=summary.summary(year, exam_type, school_number)
      data=pd.DataFrame(data,index=[0])
  
      if not data.empty:
        plot_columns=["school_name","year_of_exam","division_one","division_two","division_three","division_four","division_zero","male_students","female_students","absentees"]
        plot_data=data[plot_columns]
        file=create_plots(plot_data,image_name)
        
        if file is not None:
          school_name=data.school_name.values[0].replace("'","")
          region=data.school_region.values[0].replace("'","")
          gpa=data.gpa.values[0].replace("'","")
          
          message=f"""School Name: {school_name}\nRegion: {region}\nGPA: *{gpa}*"""
          response=save_details({
            "name":image_name,
            "file_path":file,
            "message":message,
            "caption": f"Ufaulu wa shule *{school_name}*"
          },messenger)
          
          return response
  
      return None
  except  Exception as error:
    logging.error(f"{error} while getting summary")
    return None
  pass


def autopct_format(values):
        def custom_format(pct):
            total = sum(values)
            val = int(round(pct*total/100.0))
            return '{:.1f}%\n({num:d})'.format(pct, num=val)
        return custom_format
  

def create_plots(data,file_name):
  try:
    path=os.path.join("./Imgs/Performance",f"{file_name}")
    
    fig,ax=plt.subplots(1,2,figsize=(10,5))
    # set fig color to pale green
    fig.set_facecolor("#eaeaf2")
    plot_data=data[["division_one","division_two",
                    "division_three","division_four",
                    "division_zero"]].map(lambda x: int(x))
    x_labels=["I","II","III","IV","0"]
    y=plot_data.values[0]
    ax[0].set_ylabel("Number")
    ax[0].set_xlabel("Division")
    
    # color by division
    colors=["green","blue","orange","red","black"]
    ax[0].bar(x_labels,y,color=colors,width=0.5)
    
    # plot the data on second plot using number of students
    plot_data=data[["male_students","female_students","absentees"]].map(lambda x: int(x))
    x=["Male","Female","Absentees"]
    y=(plot_data.values[0])
    # plot a pie chart on the first plot that show percentage and numbers
    ax[1].set_title("Number of students")
    ax[1].pie(y,labels=x,autopct=autopct_format(y),shadow=True,wedgeprops = {"linewidth": 1, "edgecolor": "white"})
    
    #  save plot to a file
    school_name=data.school_name.values[0].replace("'","")
    year=data.year_of_exam.values[0].replace("'","")
    fig.suptitle(f"UFAULU WA {school_name} MWAKA {year}",fontsize=14)
    plt.savefig(path)
    plt.close(fig)
    return path
  
  except Exception as error:
    logging.error(f"{error} occured while creating a plot")
    return None

def get_saved_details(image_file,messenger):
  # get saved details of the image
  try:
    collection=performance_collection.find_one({"name":image_file})
    print(collection)
    return
    if collection is not None:
      # check the timediff
      uploaded_at=collection.get("uploaded_at")
      time_difference=datetime.now()-datetime.fromtimestamp(uploaded_at)
      if time_difference >=29:
        image_path=collection.get("file_path")
        # upload_the file again
        image_id=upload_media(image_path,messenger)
        uploaded_at = datetime.timestamp(
          datetime.now(pytz.timezone("Africa/Nairobi")
                      ))
        performance_collection.update_one(
          collection,
          {"image_id":image_id,"uploaded_at":uploaded_at}
        )
        return {"image_id":image_id,
                "message":collection.get("message"),
                "caption":collection.get("caption")}
      # else for the check of days
      return {"image_id":collection.get("image_id"),
                "message":collection.get("message"),
                "caption":collection.get("caption")}
  except Exception as error:
    logging.error(f"Error {error} occured while getting saved details..")
    return None


def upload_media(image_path,messenger):
  """
  Upload media to whatsapp cloud
  """
  try:
    return messenger.upload_media(image_path).get("id")
  except Exception as error:
    logging.error(f"{error} while uploading media to cloud")
    return None

async def save_details(data,messenger):
  try:
    image_id=upload_media(data.get("file_path"))
    if image_id is not None:
      now=datetime.timestamp(datetime.now(pytz.timezone("Africa/Nairobi")))
      data["image_id"]=image_id
      data["uploaded_at"]=now
      await save_to_mongodb(data)
      
      return {"image_id":image_id,
              "message":data.get("message"),
              "caption":data.get("caption")}
  except Exception as error:
    logging.error(f"Error {error} occured while saving details")
    return None


async def save_to_mongodb(data):
  try:
    collection=performance_collection
    collection.insert_one(data)
    return True
  except Exception as error:
    logging.error(f"{error} while saving to local")
    return False
    