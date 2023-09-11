# sarufi-heyoo-blueprint

Starter code to integrating sarufi with [heyoo](https://github.com/Neurotech-HQ/heyoo).

A blueprint for deploying sarufi chabot on WhatsApp Cloud API. In this blueprint, we shall set up a webhook to receive whatsapp messages. The are several ways you can set up a webhook. I will be showing how to use and [Replit](#using-replit).


## USING REPLIT

- Log into your [Replit](https://replit.com/) account.

  Create a python repl. Download `main.py` from [Whatsapp bot using sarufi API and heyoo](https://replit.com/@neurotechafrica/sarufi-heyoo-blueprint).

  Upload/copy `main.py` code into your replit repl created. In your repl, navigate to Tools --> packages, then install `heyoo`.

  Navigate to Tools--> Secrets to create environment variables. Read [Getting whatsapp credentials](#whatsapp-cloud-creds) and [get sarufi credentials](#getting-sarufi-credentials).

  Create
  |Secrete key | Description|
  |:--- |:--- |
  |`PHONE_NUMBER_ID` | Whatsapp cloud phone ID|
  |`WHATSAPP_TOKEN` | Your whatsapp token|
  |`SARUFI_API_KEY` | Your sarufi API KEY|
  |`SARUFI_BOT_ID` | Your sarufi bot id|

- Run the script

  After creating the secret keys, run your `main.py`. A small webview window will open up with a url that looks like `https://{your repl name}.{your replit usermae}.repl.co`.

  With the url, follow simple steps at [Setting whatsapp webhook](#setting-whatsapp-webhook).

- Final touches

  Go into your repl, copy the `VERIFY_TOKEN` --> paste into verify token in your whatsapp cloud --> **verify and save**.

  We are reaching at a good point with the set-up. Lets [subscribe to message topic](#webhook-field-subscription).
  When done ,you are good to go... fire 🚀 up your bot in whatsapp by sending text.

## Whatsapp cloud creds

Navigate to `Whatsapp`-->`Getting started` to get whatsApp cloud `token` and `phone number ID` to be used.

You will have access token and phone number id.

![How to get whatsapp token and phone number ID](./readme-imgs/get_whatsapp_token.png)

## Getting Sarufi Credentials

To authorize our chabot, we are are going to use authorization keys from sarufi. Log in into your [sarufi account](https://sarufi.io). Go to your Profile on account to get Authorization keys

![Sarufi authorazation keys](./readme-imgs/sarufi_authorization.png)

## Setting whatsapp webhook

Navigate to your whatsapp cloud account --> `configuration` --> edit --> then paste the url into callback url.

![Web hook setup](./readme-imgs/webhook_setup.png)

## Webhook field subscription

After veryfing and saving whatsapp webook, navigate to webhook fields --> click `manage` to subscribe to `message` topic.

![Webhook fields subscription](./readme-imgs/webhook_subscription.png)

## Sample Bot test

With a bot deployed in Whatsapp, here is a sample of a pizza bot.
![Bot deployed in whatsapp](./readme-imgs/sample.gif)

## Issues

If you will face any issue, please raise one so as we can fix it as soon as possible

## Contribution

If there is something you would like to contribute, from typos to code to documentation, feel free to do so, `JUST FORK IT`.
