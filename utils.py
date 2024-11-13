import logging
import math
import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from nectaapi import comparison, student, summary
from PIL import Image

from Database.models import Comparison, Performance

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def structure_student_results_message(data):
  try:
    year=data.get("matokeo_year")
    exam_type= "csee" if data.get("matokeo_exam_type")== '1' else "acsee"
    school_number=(data.get("matokeo_school_number"))
    student_number=(data.get("matokeo_student_number"))

    results = student.student(year, exam_type, school_number, student_number)
    if results:
      subjects=[f"{sub} >> {score}" for sub,score in results.get("subjects").items()]
      
      message=f"""Matokeo:\nschool name:{results.get('school_name')}\ngender:{results.get('gender')}\nDivision:{results.get('division')}\nPoints:{results.get('points')}\nsubjects score: {subjects}
      """
      logging.info(f"Done structuring results message of {student_number} from {school_number}")
      return message

  except Exception as error:
    logging.error(f"{error} while structuring student results summary")
    return "Samahani sijaweza kupata matokeo yako"


async def school_summary(data:dict,messenger):
  try:
    year=data.get("ufaulu_wa_shule_year")
    exam_type= "csee" if data.get("ufaulu_wa_shule_exam_type")== '1' else "acsee"
    school_number=(data.get("ufaulu_wa_shule_school_number"))
    image_name=f"{year}_{exam_type}_{str(school_number).upper()}.png"
    
    if os.path.exists(os.path.join("./Imgs/Performance",image_name)):
      return get_saved_details(image_name,messenger,table_name="performance")
    
    # check if the school participated in exams in particular year    
    if comparison.schoolPresent(year, exam_type, school_number):
      # find results summary
      data=summary.summary(year, exam_type, school_number)
      data=pd.DataFrame(data,index=[0])
  
      if not data.empty:
        plot_columns=["school_name","year_of_exam","division_one","division_two","division_three","division_four","division_zero","male_students","female_students","absentees"]
        plot_data=data[plot_columns]
        file_path=create_performance_plots(plot_data,image_name)
        
        if file_path is not None:
          school_name=data.school_name.values[0].replace("'","")
          region=data.school_region.values[0].replace("'","")
          gpa=data.gpa.values[0].replace("'","")
          
          message=f"""School Name: {school_name}\nRegion: {region}\nGPA: *{gpa}*"""
          
          response=await save_details({
            "name":image_name,
            "file_path":file_path,
            "message":message,
            "caption": f"Ufaulu wa shule *{school_name}*"
          },messenger,table_name="performance")

          logging.info("Done obtaining school summary")
          
          return response
      return None
  except  Exception as error:
    logging.error(f"{error} while getting summary")
    return None


async def school_comparison(data,messenger):
  
  start_year=int(data.get("school_comparison_start_year"))
  end_year=int(data.get("school_comparison_end_year"))
  # check the years and swap if necessary
  if start_year > end_year:
    temp=start_year
    start_year=end_year
    end_year=temp
    
  exam_type= "csee" if data.get("school_comparison_exam_type") == "1" else "acsee"
  first_school=data.get("school_comparison_first_school")
  second_school=data.get("school_comparison_second_school")

  image_name=f"{start_year}_{end_year}_{exam_type}_{first_school.upper()}_{second_school.upper()}.png"

  try:
    base_path = "./Imgs/Comparison"
    # variant of image name
    image_name_variant=[f"{start_year}_{end_year}_{exam_type}_{second_school.upper()}_{first_school.upper()}.png",image_name]
    
    for variant_name in image_name_variant:
      if os.path.exists(os.path.join(base_path,variant_name)):
        logging.info("Loading saved data")
        return get_saved_details(variant_name,messenger,table_name="comparison")
    
    data = comparison.comparision(start_year, 
                                end_year, 
                                exam_type, 
                                [str(first_school),str(second_school)])
    
    if data is not None:
      file_path=create_comparison_plots(data,image_name)
      if file_path is not None:
        data={
          "file_path":file_path,
          "name":image_name,
          "caption": f"Ufaulu kutoka *{start_year} mpaka {end_year}*",
          "message": f"Mliganisho wa ufaulu wa shule *{first_school}* na *{second_school}*"
        }
        response=await save_details(data,messenger,table_name="comparison")
        
        logging.info("Done with school comparison")

        return response

  except Exception as error:
    logging.error(f"{error} occured in school_comparison")
    return None


def get_saved_details(image_name,messenger,table_name:str):
  # get saved details of the image
  try:
    if table_name.lower()=="performance":
      data:Performance=Performance.by_name(image_name)
    elif table_name.lower()=="comparison":
      data:Comparison=Comparison.by_name(image_name)
    logging.info("Getting Saved Details...")

    # check time diff as whatsapp keeps media[using images here] for 30 days
    time_difference=datetime.now()-data.uploaded_at
    if time_difference.days >=29:
      image_path=data.file_path
      # upload_the file again to get a new id
      image_id=messenger.upload_media(image_path).get("id")
      data.image_id=image_id
      data.uploaded_at=datetime.now()
      data.save()

      return {"image_id":image_id,
              "message":data.message,
              "caption":data.caption}
    
    # else for the check of days
    return {"image_id":data.image_id,
              "message":data.message,
              "caption":data.caption}
  except Exception as error:
    logging.error(f"Error {error} occured while getting saved details..")
    return None


async def save_details(data:dict,messenger,table_name:str):
  try:
    image_id=messenger.upload_media(data.get("file_path")).get("id")
    
    if image_id is not None:
      data["uploaded_at"]=datetime.now()
      data["image_id"]=image_id

      if table_name.lower()=="performance":
        data:Performance=Performance(**data).save()
      elif table_name.lower()=="comparison":
        data:Comparison=Comparison(**data).save()
      
      return {"image_id":image_id,
              "message":data.message,
              "caption":data.caption}
  except Exception as error:
    logging.error(f"Error {error} occured while saving details")
    return None


def add_watermark(fig,image_path="./Imgs/Watermarks/watermark.png"):
  img = Image.open(image_path)
  # resize the image
  img=img.resize((int(img.size[0]/1.5),int(img.size[1]/1.5)))
  # center the figure
  fig.figimage(img, 
               int((fig.bbox.xmax-img.size[0])/2), 
               int((fig.bbox.ymax-img.size[0])/2), 
               alpha=0.2, 
               zorder=1)
  logging.info("Added Watermark on the Plot")

  return fig


def autopct_format(values):
        def custom_format(pct):
            total = sum(values)
            val = int(round(pct*total/100.0))
            return '{:.1f}%\n({num:d})'.format(pct, num=val)
        return custom_format


def create_performance_plots(data,file_name:str):
  try:
    path=os.path.join("./Imgs/Performance",file_name)
    
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
    
    for p in ax[0].patches:
        ax[0].annotate(str(p.get_height()), (p.get_x() * 1.05, p.get_height() * 1.005))
      
    ax[0].grid(True)  
    # plot the data on second plot using number of students
    plot_data=data[["male_students","female_students","absentees"]].map(lambda x: int(x) if x != "*" else None)
    x=["Male","Female","Absentees"]
    y=(plot_data.values[0])
    # plot a pie chart on the first plot that show percentage and numbers
    ax[1].set_title("Number of students")
    ax[1].pie(y,labels=x,autopct=autopct_format(y),shadow=True,wedgeprops = {"linewidth": 1, "edgecolor": "white"})
    
    #  save plot to a file
    school_name=data.school_name.values[0].replace("'","")
    year=data.year_of_exam.values[0].replace("'","")
    
    fig=add_watermark(fig)
    
    fig.suptitle(f"UFAULU WA {school_name} MWAKA {year}",fontsize=14)
    plt.savefig(path)
    plt.close(fig)
    
    logging.info("Performance Plot created and Saved")
    return path
  
  except Exception as error:
    logging.error(f"{error} occured while creating a plot")
    return None


def create_comparison_plots(data,image_name):
  
  image_path=os.path.join("./Imgs/Comparison/",image_name)
  try:
    def generate_rows_cols(n):
      rows = math.ceil(math.sqrt(n))
      columns = math.ceil(n / rows)
      logging.info("Done Generating rows and Columns")
      return rows, columns
    
    def generate_plot_axis(ax,rows,colums):
      logging.info("Generating plot axis from rows and columns")
      # Yields the plot
      try:
        if rows==1 and columns==1:
          yield ax
        else:
          for i in range(rows):    
            if columns==1:
              yield ax[i]
            else:
              for j in range(colums):
                yield ax[i,j]

      except StopIteration as e:
        logging.error("At the end of generation of axises")
        pass

    rows,columns= generate_rows_cols(len(data))
    fig,ax=plt.subplots(rows,columns,figsize=((len(data)*4),(len(data)*3+2)))
    axis=generate_plot_axis(ax,rows,columns)
    
    fig.set_facecolor("#eaeaf2")

    for i,year in enumerate(data.keys()):
      ax=next(axis)
    
      # create a dataframe for each year
      df=pd.DataFrame(data.get(year)).T
      # convert the data to float
      df=df.map(lambda x: float(x) if x != "*" else None)
      df.plot(kind="bar",ax=ax,title=year)
  
      # Indicate values on the plot
      for p in ax.patches:
          ax.annotate(str(p.get_height()), (p.get_x() * 1.0005, p.get_height() * 1.0005))
      ax.legend(["Nafasi Kitaifa","Idadi ya wanafunzi","GPA"])
      # set the x ticks
      ax.set_xticklabels(df.index,rotation=0)
      ax.grid(True)
      # set the face color
      ax.set_facecolor("#eaeaf2")
    # remove any empty plot
    if len(data)%2!=0:
      try:
        
        ax=next(axis)
        ax.axis("off")
        ax.set_facecolor("#eaeaf2")
        logging.info("Removed any empty plot")
        
      except StopIteration:
        logging.info("Reached at the end of Generators")
    
    fig=add_watermark(fig)
      
    # set plot title
    fig.suptitle("Mlinganisho wa ufaulu",fontsize=14,fontweight="bold")
    # save the plot
    plt.savefig(image_path)
    # # close fig
    plt.close(fig)
    
    logging.info("Created and saved Comparison plot sucessfully")
    return image_path
    
  except Exception as error:
    logging.error(f"{error} while creating comparison plots")
    return None