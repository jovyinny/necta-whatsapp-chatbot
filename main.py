import os
import uvicorn
import logging
from sarufi import Sarufi
from heyoo import WhatsApp
from dotenv import load_dotenv
from typing import Optional,Dict
from fastapi import FastAPI,Response, Request,BackgroundTasks
from utils import structure_student_results_message,school_summary,school_comparison

# Initialize FastAPI App

app = FastAPI(title="Sarufi NECTA WhatsApp Bot")

load_dotenv()

# Check if all required env variables are set
if  os.getenv("WHATSAPP_TOKEN") is None:
    raise ValueError("WHATSAPP_TOKEN not set")
if  os.getenv("PHONE_NUMBER_ID") is None:
    raise ValueError("PHONE_NUMBER_ID not set")
if os.getenv("SARUFI_API_KEY") is None:
    raise ValueError("SARUFI_API_KEY not set")
if  os.getenv("SARUFI_BOT_ID") is None:
    raise ValueError("SARUFI_BOT_ID not set")
if os.getenv("VERIFY_TOKEN") is None:
    raise ValueError("VERIFY_TOKEN not set")

messenger = WhatsApp(os.getenv("WHATSAPP_TOKEN"),
                     phone_number_id=os.getenv("PHONE_NUMBER_ID"))
sarufi = Sarufi(api_key=os.getenv('SARUFI_API_KEY'))
chatbot = sarufi.get_bot(os.getenv("SARUFI_BOT_ID"))

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# FUNCTIONS
def respond(mobile: str, message: str, message_type: str = "text")->None:
    """
    Send message to user
    """
    try:
        response = sarufi.chat(
            bot_id=os.getenv("SARUFI_BOT_ID"),
            chat_id=mobile,
            message=message,
            message_type=message_type,
            channel="whatsapp",
        )
        execute_actions(actions=response, mobile=mobile)
    except Exception as error:
       logging.error("Error in respond function: %s", error)


def execute_actions(actions: dict, mobile: str)->None:
    if actions.get("actions"):
        actions = reversed(actions.get("actions"))
        for action in actions:
            
            if action.get("send_message"):
                message = action.get("send_message")
                if isinstance(message, list):
                    message = "\n".join(message)
                messenger.send_message(message=message, recipient_id=mobile)

            elif action.get("send_reply_button"):
                reply_button = action.get("send_reply_button")
                messenger.send_reply_button(button=reply_button, recipient_id=mobile)
            
            elif action.get("send_button"):
                button=action.get("send_button")
                messenger.send_button(button=button, recipient_id=mobile)
            
            elif action.get("send_images"):
              images=action.get("send_images")
              send_medias(images,mobile,"images")
              
            elif action.get("send_videos"):
              videos=action.get("send_videos")
              send_medias(videos,mobile,"videos")

            elif action.get("send_audios"):
              audios=action.get("send_audios")
              send_medias(audios,mobile,"audios")

            elif action.get("send_documents"):
              documents=action.get("send_documents")
              send_medias(documents,mobile,"documents")


            elif action.get("send_stickers"):
              stickers=action.get("send_stickers")
              send_medias(stickers,mobile,"stickers")
    
    logging.info("No response")


# send media
def send_medias(medias:dict,mobile:str ,type:str)->None:
  for media in medias:
    link=media.get("link")
    caption=media.get("caption")
    if type=="images":
       messenger.send_image(image=link,recipient_id=mobile,caption=caption )
    elif type =="videos":
      messenger.send_video(video=link,recipient_id=mobile,caption=caption)
    elif type == "audios":
      messenger.send_document(document=link,recipient_id=mobile,caption=caption)
    elif type=="stickers":
      messenger.send_sticker(sticker=link,recipient_id=mobile)
    elif type=="documents":
      messenger.send_document(document=link,recipient_id=mobile,caption=caption)
    else:
        logging.error("Unrecognized type")


# WEBHOOK ROUTE
@app.get("/")
async def wehbook_verification(request: Request):
    if request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
        content=request.query_params.get("hub.challenge")
        logging.info("Verified webhook")
        return Response(content=content, media_type="text/plain", status_code=200)
    
    logging.error("Webhook Verification failed")
    return "Invalid verification token"

@app.post("/")
async def webhook_handler(request: Request,tasks:BackgroundTasks):

    # Handle Webhook Subscriptions
    data = await request.json()
    # logging.info("Received webhook data: %s", data)
    changed_field = messenger.changed_field(data)

    if changed_field == "messages":
        new_message = messenger.is_message(data)
        if new_message:
            mobile = messenger.get_mobile(data)
            name = messenger.get_name(data)
            message_type = messenger.get_message_type(data)
            logging.info(
                f"New Message; sender:{mobile} name:{name} type:{message_type}"
            )
            # Mark message as read
            message_id = messenger.get_message_id(data)
            messenger.mark_as_read(message_id)

            if message_type == "text":
                message = messenger.get_message(data)
                name = messenger.get_name(data)
                logging.info("Message: %s", message)
                tasks.add_task(respond,
                    message=message,
                    message_type=message_type,
                    mobile=mobile,
                )

            elif message_type == "interactive":
                message_response = messenger.get_interactive_response(data)
                intractive_type = message_response.get("type")
                message_id = message_response[intractive_type]["id"]
                message_text = message_response[intractive_type]["title"]
                logging.info(f"Interactive Message; {message_id}: {message_text}")
                tasks.add_task(respond,
                    message=message_id,
                    message_type=message_type,
                    mobile=mobile,
                )
            else:
                print(f"{mobile} sent {message_type}\n{data}")
        else:
            delivery = messenger.get_delivery(data)
            if delivery:
                logging.info(f"Message : {delivery}")
            else:
                logging.info("No new message")
    return "OK",200





@app.post("/sarufi-hook")
async def webhook_sarufi(request: Request):

    # Handle Webhook Subscriptions
  data = await request.json()
  sender_id=data.get("chat_id")
  
  if data.get("matokeo"):
    response=await structure_student_results_message(data)
    messenger.send_message(
      message=response,
      recipient_id=sender_id
    )
  elif data.get("ufaulu_wa_shule"):
    summary=await school_summary(data,messenger)  
    if summary:
      image_id=summary.get("image_id")
      caption=summary.get("caption")
      message=summary.get("message")
      
      messenger.send_image(image=image_id,
                           caption=caption,
                           recipient_id=sender_id,
                          link=False)
      messenger.send_message(message=message,
                              recipient_id=sender_id)
    else:
      messenger.send_message("Samahani sijaweza kupata  taarifa",sender_id)

  elif data.get("school_comparison"):
    comparison=await school_comparison(data,messenger)
    
    if comparison:
      
      image_id=comparison.get("image_id")
      caption=comparison.get("caption")
      message=comparison.get("message")

      messenger.send_image(image=image_id,
                           caption=caption,
                           recipient_id=sender_id,
                          link=False)
      messenger.send_message(message=message,
                              recipient_id=sender_id)
    else:
      messenger.send_message("Samahani sijaweza kupata  taarifa za mlinganisho wa shule",
                             sender_id)
  else:
    messenger.send_message("Samahani sijaweza kupata matokeo",sender_id)
    
  
  return "ok",200


if __name__ == "__main__":
    # using default uvicorn port 8000
    uvicorn.run("main:app",host='0.0.0.0')