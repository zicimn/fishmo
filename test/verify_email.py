import resend

resend.api_key = "xxxx"
params = {
    "from": "你的名字 <onboarding@fishmo.top>",  # from 可以带显示名（中文也可）
    "to": ["xxxx@qq.com"],                     # ✅ to 只放纯邮箱
    "subject": "This is a test email from Resend Python SDK",
    "html": "<strong>这是一封通过 Resend Python SDK 发送的邮件。</strong>",
}

email = resend.Emails.send(params)
print(email)