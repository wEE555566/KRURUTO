from fastapi import FastAPI, Request
import hashlib, hmac, base64, json
import httpx
from fastapi.responses import PlainTextResponse
import requests
import redis
import os
import time
from datetime import datetime
import threading
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from PIL import Image
import pytesseract
import math



app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
redis_client = redis.StrictRedis(host='wee-redis', port=6379, db=0)

class UserProfile(BaseModel):
    userId: str
    userName: str
    picture: Optional[str] = None

submit_template="""
{
  "type": "bubble",
  "hero": {
    "type": "image",
    "url": "https://i.postimg.cc/BnpCHJJV/4.png",
    "size": "full",
    "aspectRatio": "2.999:1",
    "aspectMode": "fit"
  },
  "body": {
    "type": "box",
    "layout": "vertical",
    "spacing": "md",
    "contents": [
      {
        "type": "button",
        "style": "secondary",
        "action": {
          "type": "postback",
          "label": "กลับสู่หน้าหลัก",
          "data": "__back__"
        },
        "color": "#FFFFFF"
      }
    ],
    "backgroundColor": "#D1E5F4"
  }
}

"""
answer_exam_template = """
{
  "type": "bubble",
  "hero": {
    "type": "image",
    "url": "https://i.postimg.cc/rmXNFCtk/1.png",
    "aspectMode": "cover",
    "size": "full",
    "aspectRatio": "3:1"
  },
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "text",
        "text": "__question__",
        "weight": "bold",
        "size": "xl",
        "wrap": true,
        "offsetBottom": "5px"
      },
      {
        "type": "text",
        "text": "__choice1__",
        "size": "md",
        "wrap": true
      },
      {
        "type": "text",
        "text": "__choice2__",
        "size": "md",
        "wrap": true
      },
      {
        "type": "text",
        "text": "__choice3__",
        "size": "md",
        "wrap": true
      },
      {
        "type": "text",
        "text": "__choice4__",
        "size": "md",
        "wrap": true
      },
      {
        "type": "image",
        "url": "https://abdul.in.th/messaging-engine/media/images/9e5eb9e21d83e8240f5041220f772296/558708780255936906.png",
        "size": "full",
        "aspectMode": "fit",
        "aspectRatio": "6:1",
        "margin": "5px",
        "offsetTop": "5px"
      }๙
    ]
  }
}
"""

header = """
{
  "type": "bubble",
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "image",
            "url": "https://i.postimg.cc/L58vWY8P/image.png",
            "aspectMode": "cover",
            "size": "full",
            "aspectRatio": "3:1"
          }
        ]
      },

"""

score_list = """      
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "text",
                "text": "__score__",
                "size": "3xl",
                "align": "center",
                "offsetTop": "md"
              }
            ],
            "cornerRadius": "100px",
            "width": "72px",
            "height": "72px"
          },
          {
            "type": "box",
            "layout": "vertical",
            "contents": [
              {
                "type": "text",
                "contents": [
                  {
                    "type": "span",
                    "text": "__aspect__ (__full_score__)",
                    "weight": "bold",
                    "color": "#000000"
                  },
                  {
                    "type": "span",
                    "text": "     "
                  },
                  {
                    "type": "span",
                    "text": "__reason__"
                  }
                ],
                "size": "sm",
                "wrap": true
              }
            ]
          }
        ],
        "spacing": "xl",
        "paddingAll": "20px"
      }
      
      """
      
footer = """            
    ],
    "paddingAll": "0px"
  }
}


"""

exam_template = """
{
  "type": "bubble",
  "header": {
    "type": "box",
    "layout": "vertical",
    "spacing": "md",
    "contents": [
      {
        "type": "button",
        "style": "secondary",
        "color": "#FFFFFF",
        "action": {
          "type": "message",
          "label": "__joad__",
          "text": "__joad__"
        }
      }
    ],
    "backgroundColor": "#D1E5F4"
  },
  "body": {
    "type": "box",
    "layout": "vertical",
    "spacing": "md",
    "contents": [
      {
        "type": "button",
        "style": "secondary",
        "action": {
          "type": "postback",
          "data": "__choice1__",
          "label": "__correct_answer__"
        },
        "color": "#FFFFFF"
      },
      {
        "type": "button",
        "style": "secondary",
        "action": {
          "type": "postback",
          "label": "__choice2__",
          "data": "__correct_answer__"
        },
        "color": "#FFFFFF"
      },
      {
        "type": "button",
        "style": "secondary",
        "action": {
          "type": "postback",
          "label": "__choice3__",
          "data": "__correct_answer__"
        },
        "color": "#FFFFFF"
      },
      {
        "type": "button",
        "style": "secondary",
        "action": {
          "type": "postback",
          "label": "__choice4__",
          "data": "__correct_answer__"
        },
        "color": "#FFFFFF"
      }
    ],
    "backgroundColor": "#D1E5F4"
  }
}

"""

teacher_list = {
    "agent_may": {
        "name": "ครูเมย์",
        "prompt": """
            คุณคือ "ครูเมย์" ครูฟิสิกส์ผู้เชี่ยวชาญด้านการคิดวิเคราะห์และการแก้ปัญหา คุณมีประสบการณ์การสอนฟิสิกส์มากกว่า 15 ปี และได้รับรางวัลครูดีเด่นด้านนวัตกรรมการสอนฟิสิกส์
            เอกลักษณ์การสอน:

            คุณไม่เน้นการให้สูตรฟิสิกส์สำเร็จรูป แต่จะกระตุ้นให้นักเรียนเข้าใจหลักการพื้นฐานและสามารถสร้างสูตรได้ด้วยตัวเอง
            คุณมักตั้งคำถามที่ท้าทายและชวนให้นักเรียนสงสัยเกี่ยวกับปรากฏการณ์ทางฟิสิกส์รอบตัว
            คุณชอบใช้วิธีการสอนแบบโสเครติส (Socratic method) โดยตั้งคำถามที่ลึกซึ้งเกี่ยวกับกฎฟิสิกส์เพื่อนำไปสู่การค้นพบคำตอบด้วยตัวเอง
            คุณสอนแบบบูรณาการฟิสิกส์กับศาสตร์อื่น เช่น คณิตศาสตร์ ชีววิทยา และวิศวกรรม
            คุณมีความสามารถในการเชื่อมโยงทฤษฎีฟิสิกส์กับการประยุกต์ใช้ในชีวิตจริง

            ลักษณะการพูด:

            คุณพูดด้วยน้ำเสียงสุขุม มั่นใจ และมีเหตุผล
            คุณใช้คำถามปลายเปิดเสมอ เช่น "ทำไมแรงกิริยาและแรงปฏิกิริยาไม่หักล้างกัน?" "มีปัจจัยอื่นที่ส่งผลต่อความเร่งของวัตถุนี้หรือไม่?" "เราจะประยุกต์กฎการอนุรักษ์พลังงานกับสถานการณ์นี้ได้อย่างไร?"
            คุณชอบใช้คำว่า "ลองพิจารณา..." "เป็นไปได้หรือไม่ว่า..." "มีความเป็นไปได้ที่..."
            คุณมักจบการสอนด้วยโจทย์ปัญหาที่ท้าทายให้นักเรียนไปขบคิดต่อ

            การตอบคำถาม:

            เมื่อนักเรียนถามคำถามเกี่ยวกับฟิสิกส์ คุณมักไม่ให้คำตอบโดยตรง แต่จะช่วยให้พวกเขาวิเคราะห์และค้นพบคำตอบเอง
            คุณเน้นกระบวนการคิดวิเคราะห์ทางฟิสิกส์มากกว่าการจำสูตร
            คุณมักจะแสดงความชื่นชมเมื่อนักเรียนแสดงความเข้าใจในหลักการฟิสิกส์อย่างลึกซึ้ง
            
            
            ตอบกระชับถ้าคำถามสั้น และตอบแบบมีสีสันเมื่อคำถามซับซ้อน
       """
        ,
        "temperature": 0.5,
    },
    "agent_an": {
        "name": "ครูแอน",
        "prompt": """
            คุณคือ "ครูแอน" ครูฟิสิกส์ที่มีความกระตือรือร้นและหลงใหลในวิทยาศาสตร์อย่างมาก คุณจบปริญญาเอกด้านฟิสิกส์ควอนตัมและเคยทำงานในห้องปฏิบัติการวิจัยก่อนมาเป็นครูฟิสิกส์
            เอกลักษณ์การสอน:

            คุณชอบสอนฟิสิกส์ผ่านการทดลองและกิจกรรมปฏิบัติจริง
            คุณมีความรู้ลึกในเรื่องฟิสิกส์และสามารถอธิบายแนวคิดที่ซับซ้อนอย่างกลศาสตร์ควอนตัมให้เข้าใจง่าย
            คุณชอบยกตัวอย่างปรากฏการณ์ทางฟิสิกส์ในชีวิตประจำวัน เช่น อธิบายแรงเสียดทานผ่านการเล่นสเก็ตบอร์ด
            คุณเชื่อมโยงฟิสิกส์กับนวัตกรรมและเทคโนโลยีล่าสุดเสมอ เช่น เลเซอร์ ควอนตัมคอมพิวเตอร์ หรือพลังงานฟิวชัน
            คุณมีอารมณ์ขันแบบเนิร์ดและชอบเล่นมุกฟิสิกส์ เช่น "อนุภาคนิวตริโนเดินเข้าบาร์... แต่ไม่มีปฏิสัมพันธ์กับใครเลย!"

            ลักษณะการพูด:

            คุณพูดเร็วและกระตือรือร้น แสดงความตื่นเต้นกับทฤษฎีและการทดลองฟิสิกส์
            คุณชอบพูดประโยคว่า "รู้มั้ย สิ่งที่น่าสนใจมากเกี่ยวกับฟิสิกส์คือ..." "นี่เป็นปรากฏการณ์ที่น่าทึ่งมาก!" "ลองนึกภาพก้อนมวลที่เคลื่อนที่บนพื้นเอียงแบบไร้แรงเสียดทาน..."
            คุณอธิบายทฤษฎีฟิสิกส์พร้อมยกตัวอย่างการทดลองที่สนุกและเข้าใจง่าย
            คุณมักแทรกข้อเท็จจริงที่น่าสนใจเกี่ยวกับนักฟิสิกส์และการค้นพบทางฟิสิกส์ในการสอน

            การตอบคำถาม:

            คุณตื่นเต้นกับทุกคำถามเกี่ยวกับฟิสิกส์และใช้คำถามเป็นโอกาสในการขยายความรู้
            คุณชอบชวนนักเรียนตั้งสมมติฐานตามหลักการฟิสิกส์ก่อนให้คำตอบ
            คุณอาจโต้ตอบด้วยคำถามที่ท้าทายเกี่ยวกับปรากฏการณ์ทางฟิสิกส์เพื่อกระตุ้นให้คิดต่อ
            คุณชอบแนะนำวิดีโอการทดลองฟิสิกส์ที่น่าสนใจหรือเว็บไซต์จำลองสถานการณ์ทางฟิสิกส์
            
            
            ตอบกระชับถ้าคำถามสั้น และตอบแบบมีสีสันเมื่อคำถามซับซ้อน
        """
        ,
        "temperature": 0.3,
    },
    "agent_boat": {
        "name": "ครูโบ๊ท",
        "prompt": """
            คคุณคือ "ครูโบ๊ท" ครูฟิสิกส์ผู้มีความคิดสร้างสรรค์และมองโลกในแง่บวก คุณเชื่อว่าฟิสิกส์ไม่ใช่แค่สูตรและการคำนวณ แต่เป็นการเรียนรู้เกี่ยวกับความงดงามของธรรมชาติและกฎเกณฑ์ที่ควบคุมจักรวาล
            เอกลักษณ์การสอน:

            คุณสอนฟิสิกส์ด้วยใจและเน้นการสร้างความรู้สึกอัศจรรย์ใจในปรากฏการณ์ธรรมชาติ
            คุณใช้การเล่าเรื่องและอุปมาอุปไมยในการอธิบายแนวคิดทางฟิสิกส์ที่ซับซ้อน เช่น เปรียบพลังงานมืดเป็นเหมือนนักเต้นที่มองไม่เห็น
            คุณเชื่อมโยงฟิสิกส์กับศิลปะ ดนตรี ปรัชญา และประวัติศาสตร์ เช่น อธิบายคลื่นเสียงผ่านดนตรี
            คุณส่งเสริมให้นักเรียนมองเห็นความงามในสมการและทฤษฎีทางฟิสิกส์
            คุณเน้นการเข้าใจแนวคิดพื้นฐานมากกว่าการท่องจำสูตร

            ลักษณะการพูด:

            คุณพูดอย่างอ่อนโยนและมีความเป็นกันเอง ใช้ภาษาที่เข้าถึงง่าย
            คุณใช้ภาษาที่สร้างแรงบันดาลใจและกำลังใจ เช่น "แม้แต่ไอน์สไตน์ก็เคยสับสนกับทฤษฎีสัมพัทธภาพของตัวเอง" "ฟิสิกส์ควอนตัมอาจดูยาก แต่ทุกคนสามารถเข้าใจหลักการพื้นฐานได้"
            คุณมักใช้คำถามเชิงจินตนาการ เช่น "ถ้าคุณเป็นโฟตอน คุณจะรู้สึกอย่างไรที่เวลาไม่ผ่านไปเลย?"
            คุณให้คำชมที่เฉพาะเจาะจงและจริงใจเมื่อนักเรียนเข้าใจแนวคิดทางฟิสิกส์

            การตอบคำถาม:

            คุณตอบคำถามเกี่ยวกับฟิสิกส์ด้วยความเข้าใจและเปิดกว้าง ยอมรับว่าฟิสิกส์บางเรื่องยังเป็นปริศนา
            คุณมักชวนให้นักเรียนมองปัญหาทางฟิสิกส์จากมุมมองที่สร้างสรรค์
            คุณแนะนำตัวอย่างนักฟิสิกส์ที่มีแนวคิดนอกกรอบ เช่น ริชาร์ด ไฟน์แมน หรือนิลส์ โบร์
            คุณส่งเสริมให้นักเรียนทดลองคิดนอกกรอบและตั้งคำถามกับสิ่งที่เรียนปรียบการแรงเสียดทานเหมือนเวลาลื่นในเกม 
            
            
            ตอบกระชับถ้าคำถามสั้น และตอบแบบมีสีสันเมื่อคำถามซับซ้อน
        """,
        "temperature": 0.7,
    },
    "agent_dena": {
        "name": "ครูดีน่า",
            "prompt": """
                คุณคือ "ครูดีน่า" ครูพลศึกษาและการฝึกทหารที่มีบุคลิกเข้มแข็ง มีระเบียบวินัย และมุ่งมั่น คุณเป็นอดีตทหารและนักกีฬาที่ผันตัวมาเป็นครู
                เอกลักษณ์การสอน:

                คุณเน้นความมีวินัย ความมุ่งมั่น และการทำงานเป็นทีม
                คุณสอนแบบตรงไปตรงมา ไม่อ้อมค้อม
                คุณตั้งความคาดหวังสูงและกระตุ้นให้นักเรียนทำเกินขีดจำกัดของตัวเอง
                คุณเชื่อว่าความล้มเหลวเป็นส่วนหนึ่งของการเรียนรู้และความพยายามสำคัญกว่าความสามารถ
                คุณมีความเมตตาและห่วงใยนักเรียนภายใต้ท่าทีที่เข้มงวด

                ลักษณะการพูด:

                คุณพูดเสียงดังฟังชัด มั่นใจ และกระชับ
                คุณใช้คำพูดกระตุ้นและท้าทาย เช่น "ผมรู้ว่าคุณทำได้ดีกว่านี้!" "อย่ายอมแพ้!" "เหนื่อยหรือเปล่า? ดี! แสดงว่าคุณกำลังพัฒนา!"
                คุณมักใช้คำเปรียบเทียบและอุปมาอุปไมยจากกีฬาหรือการทหาร
                คุณชอบเล่าเรื่องประสบการณ์จริงและบทเรียนชีวิต

                การตอบคำถาม:

                คุณตอบคำถามตรงประเด็น ไม่อ้อมค้อม
                คุณชอบใช้ตัวอย่างที่เป็นรูปธรรมและแนวทางปฏิบัติที่ชัดเจน
                คุณมักเสริมคำตอบด้วยแรงจูงใจหรือคำท้าทาย
                คุณไม่กลัวที่จะบอกความจริงที่อาจจะไม่สบายใจ แต่ทำด้วยความเมตตา
                
                
                
                        
            """,    
        "temperature": 0.6,
    },
}


flex_leaderboard = """
{
  "type": "bubble",
  "hero": {
    "type": "image",
    "url": "https://i.postimg.cc/NFG5PwJp/5.png",
    "size": "full",
    "aspectRatio": "3:1"
  },
  "body": {
    "type": "box",
    "layout": "horizontal",
    "contents": [
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "image",
            "url": "__userpicture1__",
            "aspectRatio": "1:1",
            "aspectMode": "cover",
            "size": "sm"
          },
          {
            "type": "text",
            "text": "2",
            "align": "center",
            "size": "xl",
            "weight": "bold"
          },
          {
            "type": "text",
            "text": "__totalscore1__",
            "align": "center",
            "size": "sm",
            "color": "#6b6b6b"
          }
        ],
        "offsetTop": "15px"
      },
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "image",
            "url": "__userpicture2__",
            "aspectRatio": "1:1",
            "aspectMode": "cover",
            "size": "sm"
          },
          {
            "type": "text",
            "text": "1",
            "align": "center",
            "size": "xl",
            "weight": "bold"
          },
          {
            "type": "text",
            "text": "__totalscore2__",
            "align": "center",
            "size": "sm",
            "color": "#6b6b6b"
          }
        ]
      },
      {
        "type": "box",
        "layout": "vertical",
        "contents": [
          {
            "type": "image",
            "url": "__userpicture3__",
            "aspectRatio": "1:1",
            "aspectMode": "cover",
            "size": "sm"
          },
          {
            "type": "text",
            "text": "3",
            "align": "center",
            "size": "xl",
            "weight": "bold"
          },
          {
            "type": "text",
            "text": "__totalscore3__",
            "align": "center",
            "size": "sm",
            "color": "#6b6b6b"
          }
        ],
        "offsetTop": "15px"
      }
    ],
    "paddingAll": "13px"
  },
  "footer": {
    "type": "box",
    "layout": "vertical",
    "spacing": "md",
    "paddingAll": "25px",
    "contents": [
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "4",
            "flex": 1
          },
          {
            "type": "text",
            "text": "__name4__",
            "flex": 6
          },
          {
            "type": "text",
            "text": "__totalscore4__",
            "flex": 2,
            "align": "end"
          }
        ]
      },
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "5",
            "flex": 1
          },
          {
            "type": "text",
            "text": "__name5__",
            "flex": 6
          },
          {
            "type": "text",
            "text": "__totalscore5__",
            "flex": 2,
            "align": "end"
          }
        ]
      },
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "6",
            "flex": 1
          },
          {
            "type": "text",
            "text": "__name6__",
            "flex": 6
          },
          {
            "type": "text",
            "text": "__totalscore6__",
            "flex": 2,
            "align": "end"
          }
        ]
      },
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "7",
            "flex": 1
          },
          {
            "type": "text",
            "text": "__name7__",
            "flex": 6
          },
          {
            "type": "text",
            "text": "__totalscore7__",
            "flex": 2,
            "align": "end"
          }
        ]
      },
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "8",
            "flex": 1
          },
          {
            "type": "text",
            "text": "__name8__",
            "flex": 6
          },
          {
            "type": "text",
            "text": "__totalscore8__",
            "flex": 2,
            "align": "end"
          }
        ]
      },
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "9",
            "flex": 1
          },
          {
            "type": "text",
            "text": "__name9__",
            "flex": 6
          },
          {
            "type": "text",
            "text": "__totalscore9__",
            "flex": 2,
            "align": "end"
          }
        ]
      },
      {
        "type": "box",
        "layout": "horizontal",
        "contents": [
          {
            "type": "text",
            "text": "10",
            "flex": 1
          },
          {
            "type": "text",
            "text": "__name10__",
            "flex": 6
          },
          {
            "type": "text",
            "text": "__totalscore10__",
            "flex": 2,
            "align": "end"
          }
        ]
      }
    ]
  }
}

"""
prompt_question_1 = """ช่วยอธิบายหัวข้อ “__title__” สำหรับผู้เรียนระดับ [ระดับชั้น] โดยไม่ใช้ศัพท์เชิงวิชาการ  
อธิบายให้เหมือนพูดคุยกันในชีวิตจริง โดยเน้น:

- ทำไมเรื่องนี้จึงสำคัญ
- เรื่องนี้เกี่ยวข้องกับชีวิตประจำวันอย่างไร
- ใช้คำถามปลายเปิดกระตุ้นให้ผู้เรียนคิด เช่น “คุณเคยสงสัยไหมว่า…”

อย่าเพิ่งพูดถึงสูตรหรือทฤษฎี ขอเน้นแค่แนวคิดภาพรวมและความเชื่อมโยงกับชีวิตจริงก่อน
"""
prompt_question_2 = """ต่อจากบทเรียนหัวข้อ “__title__”  
ตอนนี้ให้เจาะลึกทฤษฎีที่เกี่ยวข้อง เช่น กฎ, หลักการพื้นฐาน, เหตุผลเชิงตรรกะของหัวข้อนี้  
กลุ่มเป้าหมายคือ [ระดับชั้น] ที่มีพื้นฐานเบื้องต้นแล้ว

อธิบาย:
- ทฤษฎีหรือหลักการหลักของเรื่องนี้ (พร้อมความหมาย)
- เหตุผลหรือกลไกเบื้องหลัง
- ถ้ามีหลายแนวคิด ให้จัดเรียงตามลำดับความเข้าใจ

ไม่ต้องยกตัวอย่างหรือโจทย์ ให้เน้น “อธิบายความคิด” แบบชัดลึกเท่านั้น
"""
prompt_question_3 = """ตอนนี้ช่วยอธิบายสูตรที่เกี่ยวข้องกับหัวข้อ “__title__”  
กลุ่มเป้าหมายคือ [ระดับชั้น] ที่กำลังเรียนเรื่องนี้ต่อจากแนวคิดและทฤษฎีแล้ว

ขอให้เนื้อหาครอบคลุม:
- สูตรหลัก พร้อมบอกชื่อ/ที่มาของสูตร  
- อธิบายความหมายของแต่ละตัวแปรในสูตร  
- ตัวอย่างการใช้สูตรแบบ step-by-step  
- ข้อผิดพลาดที่นักเรียนมักเจอเวลาใช้สูตร

อธิบายให้ชัดเจน เข้าใจง่าย และไม่เร่งรีบ
"""
prompt_question_4 = """ช่วยสร้างตัวอย่างการประยุกต์ใช้เนื้อหา “__title__”  
โดยใช้สถานการณ์จริงที่นักเรียนระดับ [ระดับชั้น] คุ้นเคย

ขอ:
- สถานการณ์จำลอง เช่น เหตุการณ์, ปัญหา, หรือสิ่งรอบตัว  
- วิเคราะห์สถานการณ์โดยใช้แนวคิดหรือสูตรที่เรียนไปแล้ว  
- อธิบายทีละขั้นตอนว่าใช้ความรู้ตรงไหน แก้ปัญหายังไง  
- หากเป็นไปได้ให้มีคำถามให้ผู้เรียนลองคิดต่อ

อย่าใช้ตัวอย่างจากตำรา ขอให้สมจริงและเชื่อมกับชีวิตประจำวัน
"""
prompt_question_5 = """ช่วยออกแบบกิจกรรมหรือแบบฝึกหัดสำหรับหัวข้อ “__title__” สำหรับนักเรียนระดับ [ระดับชั้น]

ขอ:
- สรุปสิ่งสำคัญที่เรียนไป  
- คำถามทบทวน (เชิงเข้าใจ ไม่ใช่จำ)  
- แบบฝึกหัด 3–5 ข้อ พร้อมคำแนะนำหรือแนวคำตอบ  
- คำถามสะท้อนความเข้าใจ เช่น “คุณรู้เพิ่มอะไรจากบทนี้?”

แบบฝึกควรครอบคลุมทั้งการอธิบาย, การใช้สูตร, และการเชื่อมโยงกับชีวิตจริง
"""
async def call_naja(prompt, user_input, temperature):
    url = "https://openrouter.ai/api/v1/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }
    dprompt = f"""
    {prompt}
    {user_input}
    """
    payload = {
        "model": "google/gemma-3-27b-it:free",
        "prompt": dprompt,
        "temperature": temperature,
        "max_tokens": 1000
    }

    response = requests.post(url, json=payload, headers=headers,timeout=60)
    result = response.json()['choices'][0]['text'].strip()
    return result
  
async def call_gamma(prompt, user_input, temperature):
    url = "https://openrouter.ai/api/v1/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }
    dprompt = f"""
    {prompt}
    {user_input}
    """
    payload = {
        "model": "google/gemma-3n-e4b-it:free",
        "prompt": dprompt,
        "temperature": temperature,
        "max_tokens": 1000
    }

    response = requests.post(url, json=payload, headers=headers,timeout=60)
    result = response.json()['choices'][0]['text'].strip()
    return result
  
  
  
  
  

@app.get("/text/gemma3")
async def gemma(question:str):
  prompts = f"""
  คุณคือผู้เชี่ยวชาญด้านรถยนต์ อันนี้คือคําถามที่ผู้ใช้ถามมา "{question}"
  """
  exams = await call_gamma(user_input="จงตอบคําถามต่อไปนี้",prompt=prompts ,temperature=0.8)
  return PlainTextResponse(exams)











  
@app.get("/text/gemma3_1b")
async def gemma_1b(title:str):
  prompts = f"""
  คุณคือผู้เชี่ยวชาญด้านการตั้งคำถามเพื่อกระตุ้นการเรียนรู้แบบมีส่วนร่วม โดยมีความสามารถในการออกแบบคำถามที่ช่วยให้นักเรียนเกิดการคิดวิเคราะห์ วิพากษ์ และตั้งคำถามเชิงลึกจากหัวข้อที่กำลังศึกษา

  โปรดสร้างชุดคำถามที่ใช้กระตุ้นความคิดของนักเรียน โดยอ้างอิงจากหัวข้อ {title}
  คำถามควรเริ่มจากระดับพื้นฐาน (เช่น ความเข้าใจเบื้องต้น) แล้วไล่ระดับไปสู่การประยุกต์ใช้ วิเคราะห์ และการเชื่อมโยงกับสถานการณ์จริงหรือปัญหาในชีวิตประจำวัน
  คำถามเหล่านี้ควรสามารถใช้ได้ทั้งในชั้นเรียนและการเรียนรู้ด้วยตนเอง เพื่อส่งเสริมให้ผู้เรียนสามารถต่อยอดองค์ความรู้และเข้าใจเนื้อหาได้อย่างลึกซึ้ง

  โปรดส่งผลลัพธ์เป็นรูปแบบ JSON Object (question1,question2,question3)โดยใช้ key ชื่อว่า questions ซึ่งภายในเป็นรายการคำถามที่คุณออกแบบ เช่น:

  """
  exams = await call_gamma(user_input="จงสร้างคําถามมาทั้งหมด 3 ข้อ",prompt=prompts ,temperature=0.8)
  return_exams = exams.split("```json")[1].split("```")[0]
  return_exams = json.loads(return_exams)
  return return_exams



   

@app.get("/quiz/v2")
async def quizzz(userid:str ,title: str):
    global answer_exam_template , submit_template
    add_redis_data(f"kruruto.{userid}",userid)
    number = get_redis_data(f"quiz.number.{userid}")
    if number == None:
      number = 1
    number = int(number)
      
    flex_template = answer_exam_template
    level = get_redis_data(f"level.{userid}")
    if level == None:
      level = 5
      add_redis_data(f"level.{userid}",5)
    level = int(number)
    exam = f"""
            ครูฟิสิกส์ผู้เชี่ยวชาญด้านการคิดวิเคราะห์และการแก้ปัญหา คุณมีประสบการณ์การสอนฟิสิกส์มากกว่า 15 ปี และได้รับรางวัลครูดีเด่นด้านนวัตกรรมการสอนฟิสิกส์
            คุณต้องสร้างโจทย์ปัญหามาตามเนื้อหา {title} ให้โจทย์เหมาะสมที่สุดตามเนื้อหา ความยากเต็ม10อยู่ในระดับ {level} ในรูปแบบ json object(question,options,correct_answer)
            1 ข้อ
            """

    exams = await call_naja(prompt=exam, temperature=0.7, user_input="สร้างโจทย์")
    return_exams = exams.split("```json")[1].split("```")[0]
    return_exams = json.loads(return_exams)
    finall_exam = return_exams["question"]
    print("1")
    option = f"""
คุณเป็นครูฟิสิกส์ผู้เชี่ยวชาญด้านการคิดวิเคราะห์และการแก้ปัญหา มีประสบการณ์สอนมากกว่า 15 ปี และเคยได้รับรางวัลครูดีเด่นด้านนวัตกรรมการสอนฟิสิกส์

จากโจทย์ต่อไปนี้:
"{finall_exam}"

ซึ่งอยู่ในหัวข้อ: "{title}"
ความยาก {level}

โปรดสร้างตัวเลือกคำตอบปรนัยจำนวน 4 ตัวเลือก (A, B, C, D) ให้เหมาะสมกับเนื้อหาและระดับความยากของโจทย์ พร้อมระบุคำตอบที่ถูกต้อง

รูปแบบผลลัพธ์ที่ต้องการเป็น JSON:
{{
  "options": "A: ... B: ... C: ... D: ...",
  "A": "...",
  "B": "...",
  "C": "...",
  "D": "...",
  "correct_answer": "A"  // หรือ B, C, D ตามความเหมาะสม
}}

สร้างตัวเลือกที่สมเหตุสมผล ไม่หลอกล่อจนเกินไป และแต่ละตัวเลือกควรสะท้อนถึงความเข้าใจในเนื้อหา
"""
    options = await call_naja(prompt=option, temperature=0.7, user_input="สร้าง choice")
    return_optionss = options.split("```json")[1].split("```")[0]
    return_optionss = json.loads(return_optionss)
    print("2")
    finall_choice_all = return_optionss
    finall_option = return_optionss["options"]
    finall_option_answer = return_optionss["correct_answer"]
    choiceA = return_optionss["A"]
    choiceB = return_optionss["B"]
    choiceC = return_optionss["C"]
    choiceD = return_optionss["D"]
    print("3")
    add_redis_data(f"answer_quiz.{userid}",finall_option_answer)
    flex_template = flex_template.replace("__question__", finall_exam)
    flex_template = flex_template.replace("__choice1__", choiceA)
    flex_template = flex_template.replace("__choice2__", choiceB)
    flex_template = flex_template.replace("__choice3__", choiceC)
    flex_template = flex_template.replace("__choice4__", choiceD)
    flex_template = "___TEMPLATE___" + flex_template
    number +=1
    add_redis_data(f"quiz.number.{userid}",number)
    # add_redis_data(f"quiz.userstatus.{userid}",1)
    print("4")
    return flex_template
  
# threading.Thread(target=summary_history, args=(userId, pre_message, similar)).start()


@app.get("/quiz/userinput")
async def userinput_quiz(userid: str, userinput: int,title:str):
  global answer_exam_template , submit_template
  if userinput == 1:
    userinputs = 'A'
  if userinput == 2:
    userinputs = 'B'
  if userinput == 3:
    userinputs = 'C'
  if userinput == 4:
    userinputs = 'D'
  
  number = get_redis_data(f"quiz.number.{userid}")
  number = int(number)
  add_redis_data
  number = number -1
  level = get_redis_data(f"level.{userid}")
  level = int(level)
  user_score = get_redis_data(f"quiz.total.{title}.{userid}")
  if user_score == None:
    add_redis_data(f"quiz.total.{title}.{userid}",0)
  user_score = int(user_score)
  correct_ans = get_redis_data(f"answer_quiz.{userid}")
  if correct_ans == None:
    return "DADตุย"
  
  add_redis_data("check",1)
  
  if number == 20:
    submit = submit_template
    submit = submit.replace("__back__", "kru")
    submit = "___TEMPLATE___" + submit
    add_redis_data(f"kruruto.top.{userid}.{title}.totalscore",user_score)
    add_redis_data(f"quiz.number.U13d43c31752ae57c191e70dabe73a4ce",1)
    return PlainTextResponse(submit)
  else:
    add_redis_data("check",2)
    if correct_ans == userinputs:
      user_score+=1
      level +=1
      add_redis_data(f"level.{userid}",level)
      add_redis_data("check",12)
      next_question = await quizzz(userid,title)
    else: 
      add_redis_data("check",11)
      level -=1
      add_redis_data(f"level.{userid}",level)
      next_question =  await quizzz(userid,title)
      add_redis_data("check",3)
  add_redis_data(f"quiz.total.{title}.{userid}",user_score)
  add_redis_data("check",4)
  return PlainTextResponse(next_question)
    
    
@app.get("/quiz/v2/first")
async def quizz_first(userid:str ,title: str):
  try:
    answer = await quizzz(userid,title)
    return PlainTextResponse(answer)
  except:
    return PlainTextResponse("สวัสดีจร้")
  

  
  
  
  
  
  
# @app.get("/adaptive/quiz")
# async def adaptive_quiz(userid: str, title: str):
#   global prompt_question_2 prompt_question_1 prompt_question_3 prompt_question_4 prompt_question_5
  
  
  
  
  
  
  
@app.post("/engine/rag/template")
async def rag_engine(massages: str,userid: str):
    global header, score_list, footer
    sec1, massage= massages.split("|",1)
    
    print(f"sec1: {sec1}", f"massage: {massage}", f"userid: {userid}")
    redis_client.set("userid", userid)
    
    if sec1 == "ask":
        anwer = await ask(massage,userid)
    elif sec1 == "exam":
        anwer = await exam(massage,userid)
    else:
        return PlainTextResponse("คำสั่งไม่ถูกต้อง กรุณาใช้ ask หรือ exam", status_code=400)
    print(anwer)
    return anwer


@app.get("/ask")
async def ask(message: str,userid: str):
    sec2, title, massage, kname = message.split("|")
    kru = teacher_list.get(kname)
    add_redis_data(f"check",1)
    if not kru:
        return PlainTextResponse("ครูที่คุณเลือกไม่มีในระบบ กรุณาเลือกใหม่", status_code=400)

    previous_message = get_redis_data(f"user.{userid}.chat_history")
    if previous_message == None:
        previous_message = []
    
    user_message = f"{kru['prompt']}\n\nอยู่ในเนื้อหา{title}\n\nคำถาม: {massage}"
    
    url = "https://llook.abdul.in.th/docchat/api/v1/core/chat"
    params = {
        "session_id": "xxx",
        "project_id": "kruruto",
        "user_message": user_message,
        "title": title,
        "temperature": kru['temperature'],
        "persona": kru['prompt']
    }
    headers = {"token": "interndev"}
    add_redis_data(f"check",2)

    try:
        res = requests.post(url, data=params, headers=headers)
        res.raise_for_status()
        pawee = res.json().get('content', "ไม่พบคำตอบ").replace("\n", "<br>")
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        pawee = "ขออภัย ระบบมีปัญหา ไม่สามารถตอบคำถามได้ในขณะนี้"
    add_redis_data(f"check",3)
    styled_response = f"{kru['name']} ตอบว่า: {pawee}"

    history  = []
    
    convturn = {"user": massage, "assistant": styled_response, "timestamp": datetime.now().isoformat(), "userid": userid}
    
    #get history from redis
    history = redis_client.get(f"user.{userid}.chat_history")
    
    if history:
        history = json.loads(history)
    else:
        history = []
        
    #append new message to history 
    history.append(convturn)
            
    if len(history) > 5:
        history.pop(0)
    
    #save history to redis
    redis_client.set(f"user.{userid}.chat_history", json.dumps(history))
    add_redis_data(f"check",4)

    return PlainTextResponse(styled_response)


#get user's history
@app.get("/history")
async def get_history(userid: str):
    history = redis_client.get(f"user.{userid}.chat_history")
    
    if history:
        history = json.loads(history)
    else:
        history = []
        
    return history


@app.get("/exam")
async def exam(message: str,userid:str):
    sec2, title, massage, kname = message.split("|")
    global header, score_list, footer
    kru = teacher_list.get(kname)
    if sec2 == "qa":
        responses = []
        total_score = 0
        
        score_prompt = f"""
        ครูฟิสิกส์ผู้เชี่ยวชาญด้านการคิดวิเคราะห์และการแก้ปัญหา คุณมีประสบการณ์การสอนฟิสิกส์มากกว่า 15 ปี และได้รับรางวัลครูดีเด่นด้านนวัตกรรมการสอนฟิสิกส์
        คุณได้รับคำถามจากนักเรียนเกี่ยวกับการประเมินคำถามที่สร้างขึ้นโดยนักเรียนในหัวข้อต่อไปนี้:
        {title} 
        ให้คืนสรุปผลคะแนนที่เหมาะสมที่สุดตามเกณฑ์การประเมินที่กำหนดไว้และให้เหตุผลสั้นๆ ในรูปแบบ json object(aspect,score,full_score,reason) โดยมีเกณฑ์การประเมินทั้งหมด 6 ด้าน ดังนี้:
        1. เนื้อหา
        คะแนนเต็ม 20 คะแนน โดยช่วงคะแนนคือ
        - คำถามเกี่ยวข้องโดยตรงกับเนื้อหา{title}  (15-20 คะแนน)
        - คำถามเกี่ยวข้องบางส่วนกับเนื้อหา{title}  (8-14 คะแนน)
        - คำถามไม่เกี่ยวข้องกับเนื้อหา{title}  (0-7 คะแนน)
        2. การคิดวิเคราะห์
        คะแนนเต็ม 20 คะแนน โดยช่วงคะแนนคือ
        - ส่งเสริมการคิดขั้นสูง (วิเคราะห์/สังเคราะห์/ประเมินค่า) (15-20 คะแนน)
        - ส่งเสริมการคิดขั้นกลาง (ประยุกต์ใช้/อธิบาย) (8-14 คะแนน)
        - ส่งเสริมการคิดขั้นพื้นฐาน (จำ/เข้าใจ) (0-7 คะแนน)
        3. ความชัดเจน 
        คะแนนเต็ม 15 คะแนน โดยช่วงคะแนนคือ
        - คำถามชัดเจน กระชับ และสื่อความหมายได้ดี (11-15 คะแนน)
        - คำถามเข้าใจได้แต่อาจมีความกำกวมบางส่วน (6-10 คะแนน)
        - คำถามกำกวม ไม่ชัดเจน หรือเข้าใจยาก (0-5 คะแนน)
        4. ความท้าทาย
        คะแนนเต็ม 15 คะแนน โดยช่วงคะแนนคือ
        - คำถามมีความท้าทาย กระตุ้นความสนใจ และความอยากรู้อยากเห็น (11-15 คะแนน)
        - คำถามมีความน่าสนใจพอสมควร (6-10 คะแนน)
        - คำถามไม่มีความท้าทายหรือความน่าสนใจ (0-5 คะแนน)
        5. ภาษา 
        คะแนนเต็ม 15 คะแนน โดยช่วงคะแนนคือ
        - ใช้ภาษาไทยถูกต้องตามหลักไวยากรณ์และการสะกดคำ (11-15 คะแนน)
        - ใช้ภาษาไทยถูกต้องแต่มีข้อผิดพลาดเล็กน้อย (6-10 คะแนน)
        - ใช้ภาษาไทยไม่ถูกต้องตามหลักไวยากรณ์หรือการสะกดคำ (0-5 คะแนน)
        6. ความคิดสร้างสรรค์ 
        คะแนนเต็ม 15 คะแนน โดยช่วงคะแนนคือ
        - คำถามแสดงถึงความคิดสร้างสรรค์และนวัตกรรม (11-15 คะแนน)
        - คำถามแสดงถึงความคิดสร้างสรรค์ในระดับปานกลาง (6-10 คะแนน)
        - คำถามแสดงถึงความคิดสร้างสรรค์น้อย (0-5 คะแนน)
        """
     
        answer = await call_naja(score_prompt,massage , 0.4)   
        return_answer = answer.split("```json")[1].split("```")[0]
        return_answer = json.loads(return_answer)
        
        for item in return_answer:
            score = item["score"]
            total_score += score
            responses.append(item)
        
        return_response = {
            "responses": responses,
            "total_score": total_score
        }
        
        total_score = return_response['total_score']
        responses_list = return_response['responses']
        
        
        template_score_list = ""
        
        for a in responses_list:
            aspect = a["aspect"]
            score = a["score"]
            reason = a["reason"]
            full_score = a["full_score"]
            
            score_list_tmp = score_list
            score_list_tmp  = score_list_tmp.replace('__aspect__',aspect)
            score_list_tmp  = score_list_tmp.replace('__score__',str(score))
            score_list_tmp  = score_list_tmp.replace('__reason__',reason)
            score_list_tmp  = score_list_tmp.replace('__full_score__',str(full_score))
            
            template_score_list+=score_list_tmp+"," 
            
        
        template_score_list = template_score_list[:-1]


        answer_template = "___TEMPLATE___ "+header+template_score_list+footer
        answer_template = answer_template.replace('__total_score__',str(total_score))
        add_redis_data(f"kruruto.tam.{userid}.{title}.totalscore", total_score)

        return PlainTextResponse(answer_template)
    
    elif sec2 =="quiz":
        return "ไม่สามารถสร้างคำถามได้ในขณะนี้"
      
@app.get("/all/score/tam")
async def sum_allscore_tam(userid:str):
    titles = [
        "สนามแม่เหล็กและไฟฟ้า",
        "คลื่นแม่เหล็กไฟฟ้า",
        "โลกและทรัพยากรธรรมชาติ",
        "ไฟฟ้ากระแส",
        "ไฟฟ้าสถิต"
    ]

    all_user_score=0
    for title in titles:
        try:
            user_score = get_redis_data(f"kruruto.tam.{userid}.{title}.totalscore")
            all_user_score += int(user_score)
        except:
            all_user_score += 0

    return PlainTextResponse(all_user_score)
  
@app.get("/all/score/top")
async def sum_allscore_top(userid:str):
    titles = [
        "สนามแม่เหล็กและไฟฟ้า",
        "คลื่นแม่เหล็กไฟฟ้า",
        "โลกและทรัพยากรธรรมชาติ",
        "ไฟฟ้ากระแส",
        "ไฟฟ้าสถิต"
    ]

    all_user_score = 0

    for title in titles:
        try:
            user_score = get_redis_data(f"kruruto.top.{userid}.{title}.totalscore")
            all_user_score += int(user_score)
        except:
            all_user_score += 0

    return all_user_score
  
  
  

@app.get("/leaderboard/tam")
async def leaderboard_all():
    score_list = []

    for n in range(1, 30):
        userid = get_redis_data(f"kruruto.userid.{n}")
        if not userid:
            continue  
        score_tam = sum_allscore_tam(userid)
        score_list.append((userid, int(score_tam))) 

    # เรียงจากคะแนนมากไปน้อย
    score_sorted = sorted(score_list, key=lambda x: x[1], reverse=True)

    # ดึงอันดับ 1-10 จริง ๆ
    top_10 = score_sorted[:10]

    # เติมให้ครบ 10 อันดับถ้าข้อมูลไม่พอ
    while len(top_10) < 10:
        top_10.append(("", 0))  # userid ว่าง, score = 0

    # จัดรูปแบบผลลัพธ์ให้สวย
    leaderboard = [
        {"rank": i + 1, "user": uid, "score": score}
        for i, (uid, score) in enumerate(top_10)
    ]

    return {"leaderboard": leaderboard}
  
@app.get("/leaderboard/top")
async def leaderboard_all():
    score_list = []
    for n in range(1, 30):
        try:
            userid = get_redis_data(f"kruruto.userid.{n}")
            if not userid or userid.strip() == "":
                continue  

            score_top = await sum_allscore_top(userid)    
            score_list.append((userid, int(score_top)))

        except Exception as e:
            print(f"Error at n={n}: {e}")
            continue

    score_sorted = sorted(score_list, key=lambda x: x[1], reverse=True)

    top_10 = score_sorted[:10]

    while len(top_10) < 10:
        top_10.append(("", 0))

    leaderboard = [
        {"rank": i + 1, "user": userid, "score": score}
        for i, (userid, score) in enumerate(top_10)
    ]

    return {"leaderboard": leaderboard}



@app.get("/check/total/score")
async def check_total(userid:str):
  titles = [
        "สนามแม่เหล็กและไฟฟ้า",
        "คลื่นแม่เหล็กไฟฟ้า",
        "โลกและทรัพยากรธรรมชาติ",
        "ไฟฟ้ากระแส",
        "ไฟฟ้าสถิต"
    ]
  all_user_score = 0
  
  for title in titles:   
    user_score = get_redis_data(f"kruruto.top.{userid}.{title}.totalscore") 
    if user_score == None:
      all_user_score +=0
      user_score = 0
    else:
      all_user_score += int(user_score)


  return PlainTextResponse(f"{all_user_score}")
  




@app.get("/redis/add/exam/data")
async def add_data_exam(title: str):
  
  สนามแม่เหล็กและไฟฟ้า = f"""อนุภาคแอลฟา อนุภาคบีตา รังสีแกมมา เมื่อเคลื่อนที่ในสนามแม่เหล็ก ข้อใด ไม่เกิดการเบน,ก: อนุภาคแอลฟา,ข: อนุภาคบีตา,ค: รังสีแกมมา,ง: อนุภาคแอลฟาและบีตา,3/ข้อใด ไม่ใช่สารแม่เหล็ก,ก: Mn,ข: Ni,ค: Co,ง: Na,4/เส้นแรงแม่เหล็กจะมีทิศจากใดไปยังใด,ก: จากขั้วใต้ไปขั้วเหนือ (ภายนอก),ข: จากขั้วเหนือไปขั้วใต้ (ภายนอก),ค: จากศูนย์กลางไปขั้วเหนือ,ง: จากขั้วเหนือไปศูนย์กลาง,2/อนุภาคใดจะ ไม่ ถูกแรงไฟฟ้ากระทำในสนามไฟฟ้า,ก: โปรตอน,ข: อิเล็กตรอน,ค: นิวตรอน,ง: โปรตอนและอิเล็กตรอน,3/ข้อใดคือ แรงพื้นฐานในธรรมชาติ,ก: แรงสถิต,ข: แรงกล,ค: แรงนิวเคลียร์,ง: แรงเสียดทาน,3/สนามแม่เหล็กของโลกมีประโยชน์อย่างไร,ก: ทำให้เกิดแสงเหนือ,ข: ทำให้เกิดกลางวันกลางคืน,ค: ทำให้โลกหมุน,ง: ทำให้เกิดแผ่นดินไหว,1/ตำแหน่งใดของแท่งแม่เหล็กมีความเข้มสนามแม่เหล็กมากที่สุด,ก: ปลายแท่ง,ข: กลางแท่ง,ค: รอบๆ แท่ง,ง: ไม่มีจุดใดเด่นชัด,1/สนามแม่เหล็กเป็นปริมาณใด,ก: ปริมาณสเกลาร์,ข: ปริมาณเวกเตอร์,ค: ปริมาณสมมุติ,ง: ปริมาณเฉพาะ,2/สนามแม่เหล็กสามารถตรวจจับได้ด้วย,ก: เข็มทิศ,ข: แว่นขยาย,ค: ปรอทวัดอุณหภูมิ,ง: แรงดันไฟฟ้า,1/วัสดุใดเป็นสารแม่เหล็กถาวร,ก: พลาสติก,ข: เหล็ก,ค: ทองแดง,ง: ไม้,2/เมื่อสายไฟตรงมีกระแสไหล จะเกิดสนามแม่เหล็กในลักษณะใด,ก: เป็นเส้นตรงตามสายไฟ,ข: เป็นวงกลมรอบสายไฟ,ค: เป็นวงรีรอบสายไฟ,ง: ไม่มีสนามแม่เหล็ก,2/อุปกรณ์ใดใช้หลักการของแม่เหล็กไฟฟ้า,ก: นาฬิกาทราย,ข: วิทยุ,ค: ตู้กับข้าว,ง: มีด,2/สนามแม่เหล็กสามารถเหนี่ยวนำไฟฟ้าได้ในกรณีใด,ก: วางสายไฟนิ่งในสนามแม่เหล็ก,ข: เปลี่ยนแปลงสนามแม่เหล็กผ่านวงจร,ค: หุ้มสายไฟด้วยฉนวน,ง: ต่อวงจรไฟฟ้ากับแบตเตอรี่,2/ข้อใดคือสาเหตุที่สนามแม่เหล็กของโลกเกิดขึ้น,ก: ชั้นหินเปลือกโลกเคลื่อนตัว,ข: แกนโลกหมุนและประกอบด้วยโลหะเหลว,ค: การโคจรรอบดวงอาทิตย์,ง: พลังงานแสงจากดวงอาทิตย์,2/ปริมาณของสนามแม่เหล็กวัดด้วยหน่วยใด,ก: โวลต์ (V),ข: แอมแปร์ (A),ค: เทสลา (T),ง: จูล (J),3/เมื่อสายตัวนำตรงวางในสนามแม่เหล็กและมีกระแสไฟฟ้าไหล จะเกิดอะไรขึ้น,ก: ตัวนำหายไป,ข: ตัวนำหมุนได้,ค: ตัวนำถูกผลักหรือดูด,ง: ตัวนำร้อนขึ้น,3/ขดลวดที่มีกระแสไฟฟ้าไหลสามารถสร้างอะไรได้,ก: แสง,ข: ความร้อน,ค: สนามแม่เหล็ก,ง: เสียง,3/แม่เหล็กไฟฟ้าจะมีกำลังมากขึ้นเมื่อใด,ก: เพิ่มจำนวนรอบขดลวด,ข: ลดแรงดันไฟ,ค: ใช้สายที่สั้นลง,ง: เปลี่ยนทิศกระแส,1/ข้อใดเป็นตัวอย่างของแรงแม่เหล็กไฟฟ้าในชีวิตประจำวัน,ก: พัดลมไฟฟ้า,ข: เครื่องดูดฝุ่น,ค: หลอดไฟ,ง: ทั้งหมด,4/เครื่องใช้ไฟฟ้าใดทำงานด้วยแม่เหล็กไฟฟ้า,ก: โทรทัศน์,ข: วิทยุ,ค: ลำโพง,ง: ถูกทุกข้อ,4/ประจุไฟฟ้าที่เคลื่อนที่สามารถสร้างอะไรได้,ก: คลื่นเสียง,ข: สนามแม่เหล็ก,ค: ความร้อน,ง: แรงโน้มถ่วง,2/สนามไฟฟ้ามีทิศทางจากอะไรไปหาอะไร,ก: ประจุลบไปหาประจุบวก,ข: ประจุบวกไปหาประจุลบ,ค: จุดศูนย์กลางออกด้านนอก,ง: รอบทิศทาง,2/สิ่งใดเป็นแหล่งกำเนิดสนามไฟฟ้า,ก: วัตถุที่มีมวล,ข: ประจุไฟฟ้า,ค: แม่เหล็กถาวร,ง: ตัวนำที่เป็นกลาง,2/เมื่อประจุไฟฟ้าเคลื่อนที่ในสนามแม่เหล็ก จะเกิดแรงชนิดใด,ก: แรงโน้มถ่วง,ข: แรงแม่เหล็ก,ค: แรงลอยตัว,ง: แรงเสียดทาน,2/ข้อใดต่อไปนี้สัมพันธ์กับกฎของแฟราเดย์,ก: การเกิดแสงจากสนามแม่เหล็ก,ข: การเหนี่ยวนำกระแสไฟฟ้าจากสนามแม่เหล็กที่เปลี่ยนแปลง,ค: สนามแม่เหล็กนิ่ง,ง: การนำไฟฟ้าผ่านอากาศ,2/

"""

  คลื่นแม่เหล็กไฟฟ้า = f"""
  คลื่นแม่เหล็กไฟฟ้าสามารถเกิดได้จาก,ก: นิวตรอน,ข: อิเล็กตรอน,ค: โปรตอน,ง: สนามแม่เหล็ก,4/ คลื่นแม่เหล็กไฟฟ้าทุกชนิดจะเคลื่อนที่ในสูญญากาศ โดยมีสิ่งเหมือนกันคือ,ก: ความถี่,ข: ความยาวคลื่น,ค: แอมปลิจูด,ง: อัตราเร็ว,4/ ความยาวคลื่นช่วงใดต่อไปนี้มีความยาวคลื่นสั้นที่สุด,ก: แสงสีแดง,ข: แสงสีม่วง,ค: คลื่นวิทยุ,ง: รังสีเอกซ์,4/ ถ้าสนามไฟฟ้าเกิดการเปลี่ยนแปลงจะทำให้เกิด,ก: กระแสไฟฟ้า,ข: แรงเคลื่อนไฟฟ้า,ค: สนามแม่เหล็ก,ง: แรงดัน,3/ คลื่นแม่เหล็กไฟฟ้า สามารถเคลื่อนที่ได้,ก: เพียงสุญญากาศ,ข: ผ่านก๊าซ,ค: ผ่านบริเวณที่มีสนามไฟฟ้า,ง: ผ่านได้ทุกข้อที่กล่าวข้างต้น,4/ คลื่นแม่เหล็กไฟฟ้าจะไม่นำสิ่งนี้ด้วย,ก: พลังงาน,ข: โมเมนตัม,ค: ประจุ,ง: สัญญาณจากวิทยุ,3/ ทิศทางของสนามแม่เหล็กของคลื่นแม่เหล็กไฟฟ้าจะ,ก: ขนานกับสนามไฟฟ้า,ข: ตั้งฉากกับสนามไฟฟ้า,ค: ขนานกับทิศทางการเคลื่อนที่ของคลื่น,ง: มีทิศตั้งฉากทั้งสนามไฟฟ้าและทิศการแผ่ของคลื่น,4/ สถานีวิทยุ F.M. หนึ่งประกาศว่ากระจายเสียงด้วยความถี่ 100 MHz ความยาวคลื่นในอากาศของสถานีนั้นเป็นเท่าใด,ก: 1 เมตร,ข: 2 เมตร,ค: 3 เมตร,ง: 4 เมตร,3/ แสงสีใดมีความถี่สูงสุด,ก: แดง,ข: ม่วง,ค: เขียว,ง: เหลือง,2/ ปริมาณใดต่อไปนี้ที่ปรากฏต่อผู้สังเกตเท่าเดิมเสมอ,ก: ความยาวของวัตถุ,ข: อัตราเร็ววัตถุ,ค: อัตราเร็วของแสง,ง: เวลา,3/ ข้อใดเรียงลำดับคลื่นแม่เหล็กไฟฟ้าจากความยาวคลื่นน้อยไปมากได้ถูกต้อง,ก: รังสีเอกซ์ อินฟราเรด ไมโครเวฟ,ข: อินฟราเรด รังสีเอ็กซ์ ไมโครเวฟ,ค: รังสีเอกซ์ ไมโครเวฟ อินฟราเรด,ง: ไมโครเวฟ อินฟราเรด รังสีเอกซ์,1/ มนุษย์อวกาศ 2 คนปฏิบัติภารกิจบนพื้นผิวดวงจันทร์สื่อสารกันด้วยวิธีใดจึงจะสะดวกที่สุด,ก: ตะโกนคุยกัน,ข: ใช้คลื่นโซนาร์,ค: ใช้คลื่นวิทยุ,ง: ใช้คลื่นอัลตราซาวด์,3/ คลื่นแม่เหล็กไฟฟ้าที่นิยมใช้ในรีโมทควบคุมการทำงานของเครื่องรับโทรทัศน์คือข้อใด,ก: อินฟราเรด,ข: วิทยุ,ค: ไมโครเวฟ,ง: อัลตราไวโอเลต,1/ คลื่นแม่เหล็กไฟฟ้าชนิดใดต่อไปนี้ที่มีความยาวคลื่นสั้นที่สุด,ก: อินฟราเรด,ข: ไมโครเวฟ,ค: คลื่นวิทยุ,ง: อัลตราไวโอเลต,4/ ข้อใดไม่ใช่คลื่นแม่เหล็กไฟฟ้า,ก: คลื่นในน้ำ,ข: คลื่นวิทยุ,ค: รังสีอินฟราเรด,ง: รังสีเอกซ์,1/ ข้อใดกล่าวถูกต้องเกี่ยวกับคลื่นแม่เหล็กไฟฟ้า,ก: เป็นคลื่นที่ต้องอาศัยตัวกลาง,ข: เป็นคลื่นที่อาศัยคนกลาง,ค: เป็นคลื่นที่ยืนกลางทาง,ง: เป็นคลื่นที่ไม่อาศัยตัวกลาง,4/ คลื่นแม่เหล็กไฟฟ้าที่มีอำนาจทะลุทะลวงได้มากที่สุดคือ,ก: รังสีแกมมา,ข: รังสีแกมมีท,ค: รังสีแกมแกม,ง: รังสีแกมมาเทอร์,1/ ถ้ามีความถี่คลื่นเท่ากับ 8 เฮิรตซ์ ความยาวคลื่น 8 เมตร คลื่นจะมีอัตราเร็วคลื่นเท่าไหร่,ก: 40,ข: 48,ค: 56,ง: 64,4/ คลื่นแม่เหล็กไฟฟ้าเกิดจากการเปลี่ยนแปลงของสิ่งใด,ก: สนามแม่เหล็กและสนามรถแข่ง,ข: สนามไฟฟ้าและสนามมวย,ค: สนามแม่เหล็กและสนามไฟฟ้า,ง: สนามมวยและสนามรถแข่ง,3/ ข้อใดเป็นประโยชน์ของคลื่นแม่เหล็กไฟฟ้า,ก: การสื่อสาร,ข: การมองเห็น,ค: การรักษาโรค,ง: ถูกทุกข้อ,4/ข้อใดเป็นตัวอย่างของคลื่นแม่เหล็กไฟฟ้า,ก: คลื่นเสียง,ข: คลื่นวิทยุ,ค: คลื่นน้ำ,ง: คลื่นแผ่นดินไหว,2/คลื่นแม่เหล็กไฟฟ้าเคลื่อนที่ได้ในตัวกลางใด,ก: ต้องมีอากาศเท่านั้น,ข: ต้องมีของเหลว,ค: ได้ทั้งในสุญญากาศและตัวกลาง,ง: ต้องมีโลหะ,3/แหล่งกำเนิดของคลื่นแม่เหล็กไฟฟ้าคืออะไร,ก: อิเล็กตรอนนิ่ง,ข: ประจุเคลื่อนที่,ค: วัตถุมีมวลมาก,ง: ความร้อนสูง,2/ข้อใดคือสมบัติของคลื่นแม่เหล็กไฟฟ้า,ก: ต้องมีตัวกลางในการเคลื่อนที่,ข: ไม่มีทิศทางการเคลื่อนที่,ค: เป็นคลื่นตามยาว,ง: เป็นคลื่นตามขวาง,4/ข้อใดต่อไปนี้ไม่ใช่คลื่นแม่เหล็กไฟฟ้า,ก: รังสีเอกซ์,ข: แสงอินฟราเรด,ค: คลื่นไมโครเวฟ,ง: คลื่นเสียง,4/

"""

  โลกและทรัพยากรธรรมชาติ= f"""
  โครงสร้างโลกแบ่งตามลักษณะมวลสารได้ชั้นใหญ่ๆสามชั้นอะไรบ้าง,ก: ชั้นเปลือกโลก ใต้เปลือกโลก แก่นโลก,ข: ชั้นเปลือกโลก เนื้อโลก ธรณีภาค,ค: ชั้นเปลือกโลก เนื้อโลก หินหนืด,ง: ชั้นเปลือกโลก เนื้อโลก แก่นโลก,4/ เปลือกโลกภาคพื้นทวีป ประกอบไปด้วยอะไรบ้าง,ก: ซิลิคอนและซิลิกา,ข: ซิลิคอนและอะลูมินา,ค: เหล็กและทองแดง,ง: ซิลิคอนและแมกนีเซียม,2/ เปลือกโลกแบ่งออกเป็น 2 บริเวณคือ,ก: เปลือกโลกภาคพื้นทวีปและเปลือกโลกภาคพื้นน้ำ,ข: เปลือกโลกภาคพื้นดินและเปลือกโลกภาคพื้นน้ำ,ค: เปลือกโลกชั้นนอกและเปลือกโลกชั้นใน,ง: เปลือกโลกภาคพื้นทวีปและเปลือกโลกใต้มหาสมุทร,4/ ชั้นเนื้อโลกส่วนบนกับชั้นเปลือกโลกรวมกันเรียกว่าอะไร,ก: แมนเทิล,ข: ธรณีภาค,ค: ธรณีภาคพื้นทวีป,ง: ธรณีภาคพื้นเปลือกโลก,2/ เปลือกโลกใต้มหาสมุทรประกอบด้วยธาตุอะไรบ้าง,ก: ซิลิคอนและแมกนีเซียม,ข: ซิลิคอนและซิลิกา,ค: ซิลิคอนและอะลูมินา,ง: ซิลิคอนและเหล็ก,1/ จุดกำเนิดการไหวสะเทือนของแผ่นดินไหว เรียกว่าอะไร,ก: จุดศูนย์กลางแผ่นดินไหว,ข: ศูนย์เกิดแผ่นดินไหว,ค: จุดกำเนิดของแผ่นดินไหว,ง: จุดศูนย์กลางการสั่นสะเทือนของแผ่นดิน,3/ ศูนย์เกิดแผ่นดินไหว อยู่บริเวณใด,ก: ใต้เนื้อโลก,ข: ใต้เปลือกโลก,ค: แก่นโลกชั้นใน,ง: แก่นโลกชั้นนอก,2/ ตำแหน่งบนผิวโลกที่อยู่เหนือศูนย์เกิดแผ่นดินไหว เรียกว่าอะไร,ก: จุดเหนือศูนย์กลางแผ่นดินไหว,ข: จุดเหนือศูนย์เกิดแผ่นดินไหว,ค: จุดเหนือศูนย์กำเนิดแผ่นเปลือกโลก,ง: จุดเหนือศูนย์การสั่นสะเทือนของแผ่นดินไหว,2/ ข้อใดไม่ใช่สาเหตุของการเกิดแผ่นดินไหว,ก: แผ่นดินเปลือกโลกขยายตัวและหดตัวเท่ากัน,ข: แผ่นเปลือกโลกทรุดตัวหรือยุบตัว,ค: การเกิดภูเขาไฟระเบิดอย่างรุนแรง,ง: การเคลื่อนที่ชนกันของแผ่นเปลือกโลก,1/ ปรากฏการณ์ใดเกิดขึ้นเมื่อเกิดแผ่นดินไหว,ก: เปลือกโลกทรุดตัว,ข: เปลือกโลกเกิดการกระแทกตามแนวระดับ,ค: เปลือกโลกเกิดกระทบกระแทกออกไปบริเวณรอบๆในรูปของคลื่น,ง: ถูกทุกข้อ,4/ ทฤษฎีที่ใช้อธิบายถึงกำเนิดของแผ่นดินมหาสมุทรและสิ่งมีชีวิตที่ตายทับถมอยู่ในหินบนเปลือกโลกคือทฤษฎีใด,ก: ทฤษฎีการเลื่อนไหลของทวีป,ข: ทฤษฎีการขยายตัวของพื้นทวีป,ค: ทฤษฎีแปรสัณฐานแผ่นธรณีภาค,ง: ผิดทุกข้อ,3/ หลักฐานที่นักธรณีวิทยาและนักวิทยาศาสตร์ เชื่อว่าโลกของเรามีกระบวนการเปลี่ยนแปลงตลอดเวลา,ก: การปรากฏรอยแตกของเปลือกโลก,ข: การเกิดแผ่นดินไหว,ค: การเกิดภูเขาและภูเขาไฟ,ง: ถูกทุกข้อ,4/ สาเหตุที่ทำให้เปลือกโลกเคลื่อนที่คือข้อใด,ก: การประทุของหินแข็งในชั้นเปลือกโลก,ข: การไหลของหินหนืดในชั้นเนื้อโลก,ค: การเคลื่อนที่ของแร่ธาตุในแก่นโลกชั้นใน,ง: การแทรกตัวขึ้นมาของแร่ธาตุจากแก่นโลกชั้นนอก,2/ แผ่นดินของทวีปอเมริกากับทวีปยุโรปและทวีปแอฟริกาแยกห่างกันมากขึ้นตลอดเวลา เพราะสาเหตุใด,ก: แผ่นเปลือกโลกเคลื่อนที่เนื่องจากการไหลของแมกมาในชั้นเนื้อโลก,ข: หินหนืดในชั้นเนื้อโลกดันแทรกขึ้นมาตามรอยแตกระหว่างเปลือกโลก,ค: เกิดการแทรกตัวของภูเขาไฟและแผ่นดินในบริเวณชั้นนี้บ่อยครั้ง,ง: ข้อ ก. และ ข. ถูก,4/ ผิวโลกในบริเวณต่างๆมีลักษณะเป็นอย่างไร,ก: ที่ราบมีลักษณะเหมือนกัน,ข: ส่วนที่เป็นภูเขามีลักษณะเหมือนกัน,ค: มีความแตกต่างกันตามลักษณะภูมิประเทศ,ง: ส่วนที่เป็นพื้นน้ำจะมีอุณหภูมิปกติเหมือนกัน,3/ เทือกเขาแอลป์ในทวีปยุโรป เกิดจากแผ่นธรณีใด,ก: แผ่นธรณีภาคใต้มหาสมุทรกับแผ่นธรณีภาคใต้มหาสมุทร,ข: แผ่นธรณีภาคใต้มหาสมุทรกับแผ่นธรณีภาคพื้นทวีป,ค: แผ่นธรณีภาคใต้มหาสมุทรกับแผ่นธรณีใต้มหาสมุทร,ง: แผ่นธรณีภาคพื้นทวีปกับแผ่นธรณีภาคพื้นทวีป,4/ สนามแม่เหล็กโบราณใช้เป็นหลักฐานเพื่อพิสูจน์อะไร,ก: การแปรสัณฐานแผ่นธรณีภาค,ข: การเคลื่อนที่ของธรณีภาค,ค: แม่เหล็กโลกปัจจุบัน,ง: ข้อ ก. และ ข. ถูก,4/ ปัจจุบันแผ่นเปลือกโลกที่รองรับทวีปอเมริกา ทวีปยุโรป และทวีปแอฟริกา มีการเคลื่อนที่อย่างไร,ก: เคลื่อนที่เข้าหากัน,ข: เคลื่อนที่แยกออกจากกัน,ค: เคลื่อนที่ในทิศที่แตกต่างกัน,ง: ยังไม่มีการเคลื่อนที่แต่อย่างไร,2/ หินหนืดที่พ่นออกจากภูเขาไฟ เป็นสารที่มาจากชั้นใดของโลก,ก: ชั้นเปลือกโลก,ข: ชั้นแมนเทิล,ค: ชั้นแก่นโลก,ง: ทุกชั้นรวมกัน,2/ ชั้นใดของโลกที่มีความหนามากที่สุด,ก: แก่นโลก,ข: แมนเทิล,ค: เปลือกโลก,ง: ผิวโลก,2/ทรัพยากรธรรมชาติชนิดใดใช้แล้วหมดไป,ก: พลังงานแสงอาทิตย์,ข: น้ำฝน,ค: น้ำมันดิบ,ง: ลม,3/กระบวนการใดทำให้เกิดการเปลี่ยนแปลงของเปลือกโลก,ก: การหมุนของโลก,ข: การเคลื่อนตัวของแผ่นเปลือกโลก,ค: การระเหยของน้ำ,ง: การเกิดฝน,2/ข้อใดคือทรัพยากรธรรมชาติที่มนุษย์นำมาใช้ผลิตกระแสไฟฟ้า,ก: ถ่านหิน,ข: ดินเหนียว,ค: พืชสวน,ง: ทราย,1/การอนุรักษ์ป่าไม้ควรทำอย่างไร,ก: ตัดไม้ให้มากขึ้น,ข: ใช้ป่าไม้ให้คุ้มค่า,ค: ปลูกป่าทดแทน,ง: ขยายพื้นที่เกษตร,3/ข้อใดคือประโยชน์ของทรัพยากรน้ำ,ก: ทำให้เกิดแผ่นดินไหว,ข: เป็นที่อยู่อาศัยของสัตว์น้ำ,ค: ทำให้เกิดภูเขา,ง: ทำให้เปลือกโลกเคลื่อน,2/
"""

  ไฟฟ้ากระแส = f"""ในแท่งตัวนำหนึ่งๆ ที่มีกระแสไฟฟ้าซึ่งมีค่ามากกว่าศูนย์ไหลผ่าน ข้อต่อไปนี้ข้อใดผิด, ก: กระแสอิเล็กตรอนมีทิศทางเดียวกับสนามไฟฟ้า, ข: กระแสอิเล็กตรอนเคลื่อนที่จากศักย์ต่ำไปยังศักย์สูง, ค: กระแสไฟฟ้ามีทิศตรงข้ามกับกระแสอิเล็กตรอน, ง: สนามไฟฟ้าในตัวนำนี้มีค่ามากกว่าศูนย์, 1/ เมื่อทำให้ปลายทั้งสองข้างของแท่งโลหะมีความต่างศักย์จะมี, ก: การเคลื่อนที่ของอิเล็กตรอนอิสระในแท่งโลหะ, ข: การถ่ายเทประจุไฟฟ้าผ่านพื้นที่หน้าตัด, ค: กระแสไฟฟ้าไหลผ่านแท่งโลหะ, ง: การเคลื่อนที่ของประจุไฟฟ้าบวกและลบ, 3/ การนำไฟฟ้าในโลหะและอิเล็กโทรไลต์ ข้อใดถูก, ก: ข้อ 1 และ 2, ข: ข้อ 2 และ 3, ค: ข้อ 1 และ 3, ง: ข้อ 1 2 และ 3, 1/ คำกล่าวต่อไปนี้ข้อใดถูกต้อง, ก: โซเดียมไอออนจะจับที่ขั้วบวก, ข: ประจุบวกและลบเคลื่อนที่ในโลหะ, ค: อิเล็กตรอนหลุดจากแคโทดในสุญญากาศ, ง: ประจุลบเคลื่อนที่ตรงข้ามสนามไฟฟ้า, 3/ ข้อใดผิด, ก: การเคลื่อนที่ของอิเล็กตรอนอิสระ, ข: การเคลื่อนที่ของประจุบวกและลบ, ค: หลอดนีออนมีเฉพาะอิเล็กตรอนอิสระ, ง: แอโนดกับขั้วลบจะไม่เกิดกระแส, 3/ ข้อความในข้อใดผิด, ก: กระแสไฟฟ้าในอิเล็กโทรไลต์เกิดจากไอออน, ข: หลอดก๊าซมีอิเล็กตรอนและไอออนบวก, ค: โลหะเกิดจากอิเล็กตรอนอิสระ, ง: สารกึ่งตัวนำไม่มีอิเล็กตรอนอิสระ, 4/ กระแสไฟฟ้า 2 A ไหลในลวด 4 นาที อิเล็กตรอนที่ถ่ายเทกี่อนุภาค, ก: 1.5×10^21, ข: 2.0×10^21, ค: 3.0×10^21, ง: 8.0×10^21, 4/ ประจุ +120 C จากขั้วบวก และ –240 C จากขั้วลบ ในเวลา 1 นาที กระแสไฟฟ้าเท่าไร, ก: 2 A, ข: 3 A, ค: 6 A, ง: 12 A, 3/ อิเล็กตรอนอิสระ 2×10^19 อนุภาคใน 4 วินาที กระแสไฟฟ้าเท่าไร, ก: 0.2 A, ข: 0.8 A, ค: 3.2 A, ง: 12.8 A, 2/ ลวดมีหน้าตัด 0.1 cm² n = 5×10^28 v = 5×10^–6 m/s I เท่าไร, ก: 0.5 A, ข: 0.4 A, ค: 0.3 A, ง: 0.1 A, 2/ ประโยค “กระแสแปรผันตรงกับแรงดัน และผกผันกับความต้านทาน” เป็นของใคร, ก: โดคยองซู, ข: ไอแซก นิวตัน, ค: อองเตร แอมแปร์, ง: จอร์จ โอห์ม, 4/ ถ้าเพิ่มค่าความต้านทานในวงจร กระแสไฟฟ้าจะเป็นอย่างไร, ก: เพิ่มขึ้น, ข: ลดลง, ค: คงที่, ง: เพิ่มขึ้นแล้วลดลง, 2/ โทรศัพท์ใช้ 300 mA ได้นาน 6 ชั่วโมง ประจุไฟฟ้าเท่าไร, ก: 1 800 C, ข: 6 480 C, ค: 64 800 000 C, ง: 1.8 C, 2/ ถ้าต้องการวัดกระแสไฟฟ้า ใช้อุปกรณ์ใด, ก: โอห์มมิเตอร์, ข: โวลต์มิเตอร์, ค: เทอร์โมมิเตอร์, ง: แอมป์มิเตอร์, 4/ ข้อใดกล่าวผิด, ก: กระแสไฟฟ้าเกิดจากอิเล็กตรอน, ข: แอมแปร์คือหน่วยของกระแส, ค: คำนวณจากประจุในหนึ่งเวลา, ง: ตัวนำคือวัตถุที่มีความต้านทานสูง, 4/ ความเร็วลอยเลื่อนคือ, ก: ความเร็วเฉลี่ยของอิเล็กตรอนในลวดเพราะสนามไฟฟ้า, ข: เพราะสนามแม่เหล็ก, ค: ใช้ในการเคลื่อนที่รอบเดียว, ง: –, 1/ ลวดทองแดงหน้าตัด 1 mm² v = 10 V e = E n = 10^28 กระแสไฟฟ้าเท่าไร, ก: 1 BEv, ข: 0.1 BEv, ค: 100 BEv, ง: –, 2/ เมื่อความต่างศักย์เพิ่มขึ้น กระแสจะ, ก: ลดลง, ข: เพิ่มขึ้น, ค: คงที่, ง: ลดลงแล้วเพิ่มขึ้น, 2/ ตัวนำที่ดีต้องมีคุณสมบัติใด, ก: ความต้านทานสูง, ข: นำไฟฟ้าได้ดี, ค: ความจุไฟฟ้าสูง, ง: มีความเหนี่ยวนำต่ำ, 2/ อุปกรณ์ที่ใช้ตรวจจับกระแสขนาดเล็กมากคือ, ก: กัลวานอมิเตอร์, ข: แอมป์มิเตอร์, ค: โอห์มมิเตอร์, ง: โวลต์มิเตอร์, 1/กระแสไฟฟ้าเกิดจากอะไร,ก: การไหลของอากาศ,ข: การไหลของประจุไฟฟ้า,ค: การเคลื่อนที่ของแม่เหล็ก,ง: การหมุนของโลก,2/หน่วยของความต่างศักย์ไฟฟ้าคืออะไร,ก: แอมแปร์ (A),ข: โอห์ม (Ω),ค: โวลต์ (V),ง: วัตต์ (W),3/อุปกรณ์ใดใช้วัดกระแสไฟฟ้า,ก: โวลต์มิเตอร์,ข: แอมป์มิเตอร์,ค: โอห์มมิเตอร์,ง: เทอร์โมมิเตอร์,2/ตัวนำไฟฟ้าที่ดีควรมีสมบัติอย่างไร,ก: ความต้านทานสูง,ข: เป็นฉนวน,ค: ความต้านทานต่ำ,ง: เป็นของแข็งเท่านั้น,3/สิ่งใดเป็นแหล่งกำเนิดไฟฟ้ากระแสตรง,ก: ไดนาโม,ข: แผงโซลาร์เซลล์,ค: หม้อแปลงไฟฟ้า,ง: เครื่องทำน้ำอุ่น,2/
"""
  ไฟฟ้าสถิต = f"""ในแท่งตัวนำหนึ่งๆ ที่มีกระแสไฟฟ้าซึ่งมีค่ามากกว่าศูนย์ไหลผ่าน ข้อต่อไปนี้ข้อใดผิด,ก: กระแสอิเล็กตรอนมีทิศทางเดียวกับสนามไฟฟ้า,ข: กระแสอิเล็กตรอนเคลื่อนที่จากศักย์ต่ำไปยังศักย์สูง,ค: กระแสไฟฟ้ามีทิศตรงข้ามกับกระแสอิเล็กตรอน,ง: สนามไฟฟ้าในตัวนำนี้มีค่ามากกว่าศูนย์,1/เมื่อทำให้ปลายทั้งสองข้างของแท่งโลหะมีความต่างศักย์จะมี,ก: การเคลื่อนที่ของอิเล็กตรอนอิสระในแท่งโลหะ,ข: การถ่ายเทประจุไฟฟ้าผ่านพื้นที่หน้าตัด,ค: กระแสไฟฟ้าไหลผ่านแท่งโลหะ,ง: การเคลื่อนที่ของประจุไฟฟ้าบวกและลบ,3/การนำไฟฟ้าในโลหะและอิเล็กโทรไลต์ ข้อใดถูก,ก: ข้อ 1 และ 2,ข: ข้อ 2 และ 3,ค: ข้อ 1 และ 3,ง: ข้อ 1 2 และ 3,1/คำกล่าวต่อไปนี้ข้อใดถูกต้อง,ก: โซเดียมไอออนจะจับที่ขั้วบวก,ข: ประจุบวกและลบเคลื่อนที่ในโลหะ,ค: อิเล็กตรอนหลุดจากแคโทดในสุญญากาศ,ง: ประจุลบเคลื่อนที่ตรงข้ามสนามไฟฟ้า,3/ข้อใดผิด,ก: การเคลื่อนที่ของอิเล็กตรอนอิสระ,ข: การเคลื่อนที่ของประจุบวกและลบ,ค: หลอดนีออนมีเฉพาะอิเล็กตรอนอิสระ,ง: แอโนดกับขั้วลบจะไม่เกิดกระแส,3/ข้อความในข้อใดผิด,ก: กระแสไฟฟ้าในอิเล็กโทรไลต์เกิดจากไอออน,ข: หลอดก๊าซมีอิเล็กตรอนและไอออนบวก,ค: โลหะเกิดจากอิเล็กตรอนอิสระ,ง: สารกึ่งตัวนำไม่มีอิเล็กตรอนอิสระ,4/กระแสไฟฟ้า 2 A ไหลในลวด 4 นาที อิเล็กตรอนที่ถ่ายเทกี่อนุภาค,ก: 1.5×10^21,ข: 2.0×10^21,ค: 3.0×10^21,ง: 8.0×10^21,4/ประจุ +120 C จากขั้วบวก และ -240 C จากขั้วลบ ในเวลา 1 นาที กระแสไฟฟ้าเท่าไร,ก: 2 A,ข: 3 A,ค: 6 A,ง: 12 A,3/อิเล็กตรอนอิสระ 2×10^19 อนุภาคใน 4 วินาที กระแสไฟฟ้าเท่าไร,ก: 0.2 A,ข: 0.8 A,ค: 3.2 A,ง: 12.8 A,2/ลวดมีหน้าตัด 0.1 cm² n = 5×10^28 v = 5×10^–6 m/s I เท่าไร,ก: 0.5 A,ข: 0.4 A,ค: 0.3 A,ง: 0.1 A,2/ประโยค ‘กระแสแปรผันตรงกับแรงดัน และผกผันกับความต้านทาน’ เป็นของใคร,ก: โดคยองซู,ข: ไอแซก นิวตัน,ค: อองเตร แอมแปร์,ง: จอร์จ โอห์ม,4/ถ้าเพิ่มค่าความต้านทานในวงจร กระแสไฟฟ้าจะเป็นอย่างไร,ก: เพิ่มขึ้น,ข: ลดลง,ค: คงที่,ง: เพิ่มขึ้นแล้วลดลง,2/โทรศัพท์ใช้ 300 mA ได้นาน 6 ชั่วโมง ประจุไฟฟ้าเท่าไร,ก: 1 800 C,ข: 6 480 C,ค: 64 800 000 C,ง: 1.8 C,2/ถ้าต้องการวัดกระแสไฟฟ้า ใช้อุปกรณ์ใด,ก: โอห์มมิเตอร์,ข: โวลต์มิเตอร์,ค: เทอร์โมมิเตอร์,ง: แอมป์มิเตอร์,4/ข้อใดกล่าวผิด,ก: กระแสไฟฟ้าเกิดจากอิเล็กตรอน,ข: แอมแปร์คือหน่วยของกระแส,ค: คำนวณจากประจุในหนึ่งเวลา,ง: ตัวนำคือวัตถุที่มีความต้านทานสูง,4/ลวดทองแดงหน้าตัด 1 mm² v = 10 V e = E n = 10^28 กระแสไฟฟ้าเท่าไร,ก: 1 BEv,ข: 0.1 BEv,ค: 100 BEv,ง: –,2/เมื่อความต่างศักย์เพิ่มขึ้น กระแสจะ,ก: ลดลง,ข: เพิ่มขึ้น,ค: คงที่,ง: ลดลงแล้วเพิ่มขึ้น,2/ตัวนำที่ดีต้องมีคุณสมบัติใด,ก: ความต้านทานสูง,ข: นำไฟฟ้าได้ดี,ค: ความจุไฟฟ้าสูง,ง: มีความเหนี่ยวนำต่ำ,2/ตัวนำไฟฟ้าชนิดใดที่นิยมใช้ในงานอิเล็กทรอนิกส์เพราะมีความต้านทานต่ำ,ก: ทองแดง,ข: เหล็ก,ค: อะลูมิเนียม,ง: พลาสติก,1/ไฟฟ้าสถิตเกิดจากอะไร,ก: ประจุไฟฟ้าเคลื่อนที่,ข: ประจุไฟฟ้านิ่งสะสมอยู่,ค: สนามแม่เหล็ก,ง: การใช้ไฟฟ้ากระแสตรง,2/เมื่อวัตถุมีประจุต่างกันมาสัมผัสกันจะเกิดอะไรขึ้น,ก: ดึงดูดกัน,ข: ผลักกัน,ค: ไม่เกิดอะไรขึ้น,ง: ละลาย,1/อุปกรณ์ใดใช้ตรวจวัดไฟฟ้าสถิต,ก: มัลติมิเตอร์,ข: แอมป์มิเตอร์,ค: โวลต์มิเตอร์,ง: อิเล็กโตรสโคป,4/การถูวัตถุต่างชนิดกันสามารถทำให้เกิดอะไร,ก: ความร้อน,ข: แรงโน้มถ่วง,ค: ไฟฟ้าสถิต,ง: สนามแม่เหล็ก,3/วัตถุที่เป็นกลางทางไฟฟ้ามีลักษณะอย่างไร,ก: มีแต่ประจุบวก,ข: มีแต่ประจุลบ,ค: มีประจุทั้งบวกและลบเท่ากัน,ง: ไม่มีประจุเลย,3/
"""


  if title == "ไฟฟ้ากระแส":
      raw = f"{ไฟฟ้ากระแส}"
  elif title == "ไฟฟ้าสถิต":  
      raw = f"{ไฟฟ้าสถิต}"
  elif title == "โลกและทรัพยากรธรรมชาติ":
      raw = f"{โลกและทรัพยากรธรรมชาติ}"
  elif title == "คลื่นแม่เหล็กไฟฟ้า":
      raw = f"{คลื่นแม่เหล็กไฟฟ้า}"
  elif title == "สนามแม่เหล็กและไฟฟ้า":
      raw = f"{สนามแม่เหล็กและไฟฟ้า}"
  else:
      raise ValueError("Title not found")

  # hash สำหรับ namespace
  titles = hashlib.sha256(title.encode()).hexdigest()

  # แยกแต่ละข้อโดย "/" แล้วตัดช่องสุดท้ายถ้าว่าง
  questions = [q for q in raw.split("/") if q.strip()]
  max_q = 20

  for idx, qa in enumerate(questions[:max_q], start=1):
      # แต่ละ qa รูปแบบ: "โจทย์,ช้อย1,ช้อย2,ช้อย3,ช้อย4,คำตอบ"
      parts = [p.strip() for p in qa.split(",")]
      if len(parts) != 6:
          # ถ้าไม่ครบ 6 ชิ้น แสดงข้อผิดพลาด
          print(f"Warning: ข้อที่ {idx} แยกไม่ได้ครบ 6 ส่วน -> {parts}")
          continue

      question, choice1, choice2, choice3, choice4, answer = parts

      # เก็บลง redis
      add_redis_data(f"kruruto.{titles}.question.{idx}", question)
      add_redis_data(f"kruruto.{titles}.choice1.{idx}", choice1)
      add_redis_data(f"kruruto.{titles}.choice2.{idx}", choice2)
      add_redis_data(f"kruruto.{titles}.choice3.{idx}", choice3)
      add_redis_data(f"kruruto.{titles}.choice4.{idx}", choice4)
      add_redis_data(f"kruruto.{titles}.answer.{idx}", answer)
  return PlainTextResponse(f"มีอะไรสามารถถามครูได้เลยนะคับ เรากําลังเรียนเรื่อง : {title}")
 

@app.post("/redis/add/data")
async def add_data(key: str, value: str):
    if not key or not value:
        return PlainTextResponse("Key and value are required", status_code=400)
    add_redis_data(key, value)
    return PlainTextResponse(f"Data added: {key} -> {value}")


@app.get("/redis/get/data")
async def get_data(key: str):
    if not key:
        return PlainTextResponse("Key is required", status_code=400)
    # value = redis_client.get(key)
    
    value = get_redis_data(key)
    
    return {key: value} if value else PlainTextResponse("Key not found", status_code=404)


def get_redis_data(key: str):
    
    print('get key',key)
    value = redis_client.get(key)
    
    if value is None:
        return None
      
    print('get value',value)

    return value.decode('utf-8')


def add_redis_data(key: str, value: str):
    
    try:
      redis_client.set(key, value)
    except redis.exceptions.ConnectionError as e:
      print('redis add error',str(e))
    return True


#delete all data in redis
@app.delete("/redis/data/all")
async def delete_all_data():
  redis_client.flushdb()  
    
    
  return True


@app.delete("/redis/delete/data/select")
async def delete_data(key: str):
    if not key:
        return PlainTextResponse("Key is required", status_code=400)
    redis_client.delete(key)
    return PlainTextResponse(f"Data deleted: {key}")

#show all data in redis
@app.get("/redis/show/alldata")
async def show_all_data():
    keys = redis_client.keys()
    all_data = {}
    for key in keys:
        value = redis_client.get(key)
        all_data[key.decode('utf-8')] = value.decode('utf-8')
    return PlainTextResponse(str(all_data))


@app.post("/user/profile")
async def add_user_profile(user_profile: UserProfile):
    user_profile_dict = user_profile.dict()

    userid = user_profile_dict["userId"]
    redis_client.set(f'user.{userid}.profile', json.dumps(user_profile_dict))
    redis_client.set(f'user.{userid}.name', user_profile_dict["userName"])
    redis_client.set(f'user.{userid}.picture', user_profile_dict["picture"])
    return PlainTextResponse(f"User profile added: {user_profile_dict}")
  
  
@app.get("/start/user/")
async def get_user_profile(userId: str, userName: str, picture: str):
    if not userId or not userName or not picture:
        return PlainTextResponse("userId, userName and picture are required", status_code=400)
    
    user_profile = {
        "userId": userId,
        "userName": userName,
        "picture": picture
    }
    
    add_redis_data(f'user.{userId}.profile', json.dumps(user_profile))
    add_redis_data(f'user.{userId}.name', userName)
    add_redis_data(f'user.{userId}.picture', picture)
    
    return PlainTextResponse(f"User profile added: {user_profile}")
  

@app.get("/start/t1/flex")
async def flex_get_data(title:str, i:str):
  global answer_exam_template
  titles = hashlib.sha256(title.encode()).hexdigest()

  answer_exam_template_n = answer_exam_template

  question = get_redis_data(f"kruruto.{titles}.question.{i}")
  choice1  = get_redis_data(f"kruruto.{titles}.choice1.{i}")
  choice2  = get_redis_data(f"kruruto.{titles}.choice2.{i}")
  choice3  = get_redis_data(f"kruruto.{titles}.choice3.{i}")
  choice4  = get_redis_data(f"kruruto.{titles}.choice4.{i}")


 
  answer_exam_template_n = answer_exam_template_n.replace("__question__", question)
  answer_exam_template_n = answer_exam_template_n.replace("__choice1__", choice1)
  answer_exam_template_n = answer_exam_template_n.replace("__choice2__", choice2)
  answer_exam_template_n = answer_exam_template_n.replace("__choice3__", choice3)
  answer_exam_template_n = answer_exam_template_n.replace("__choice4__", choice4)

  return answer_exam_template_n


@app.get("/user/get/line")
async def get_user_line(userid: str, title: str, user_answer: str):

    titles = hashlib.sha256(title.encode()).hexdigest()
    user_sessionid = get_redis_data(f"kruruto.{userid}.sessionid") 
    question_number = get_redis_data(f"kruruto.{userid}.{user_sessionid}.status")
    real_answer = get_redis_data(f"kruruto.{titles}.answer.{question_number}")
    question_number=int(question_number)

    if real_answer == user_answer:
      if question_number == 20:
        total_score = await get_total_score(userid, title)
        add_redis_data(f"kruruto.top.{userid}.{title}.score", total_score)
        add_redis_data(f"kruruto.{userid}.{user_sessionid}.status", "1")
        submit = submit_template
        submit = submit.replace("__back__", "kru")
        submit = "___TEMPLATE___" + submit
        return PlainTextResponse(submit)
      print("answer correct")
      add_redis_data(f"kruruto.{userid}.{user_sessionid}.{question_number}.score",1)
      new = await get_user(userid, title)
      return PlainTextResponse(new)
      
    else:
        print("answer incorrect")
        add_redis_data(f"kruruto.{userid}.{user_sessionid}.{question_number}.score",0)
        new = await get_user(userid, title)
        return PlainTextResponse(new)
      
      
      

@app.get("/start/ti/user_getquestion")
async def get_user(userid: str, title: str):
  global submit_template
  n = get_redis_data(f"kuruto.userid.check")
  if n == None:
    n = 1
    add_redis_data(f"kuruto.userid.check", n)
  n = int(n)
  user_profile = get_redis_data(f"kuruto.userid.{n}")
  if user_profile == None:
    add_redis_data(f"kuruto.userid.{n}", userid)
    n+=1
    add_redis_data(f"kuruto.userid.check", n)
    
  try:
    wee = await get_user_input(userid, title)
    return (wee)
  except:
    submit = submit_template
    submit = submit.replace("__back__", "kru")
    submit = "___TEMPLATE___" + submit
    user_sessionid = get_redis_data(f"kruruto.{userid}.sessionid") 
    add_redis_data(f"kruruto.{userid}.{user_sessionid}.status", "1")
    return (submit)

  

    
@app.get("/start/ti/user_getquestion/wee")
async def get_user_input(userid:str, title:str):
  titles = hashlib.sha256(title.encode()).hexdigest()
  add_redis_data(f"kruruto.userid.", userid)
  user_session_key = f"kruruto.{userid}.sessionid"
  
  # status_sesionid = False
  # check_sessionid = False
  
  session_status = 0
  sessionid_hash = ""
  #check if user in session // get sessionid from redis with user "kuruto.{userid}.sessionid"  
  user_sessionid = get_redis_data(user_session_key) 

  #if user not in session, then set sessionid to "kuruto.{userid}.sessionid" 
  
  print('user_session',user_sessionid)
  
  if user_sessionid == None:
    sessionid=f"{title}{userid}.{datetime.now().isoformat()}"
    sessionid_hash = hashlib.sha256(sessionid.encode()).hexdigest()
    add_redis_data(user_session_key, sessionid_hash)
    user_sessions_status_key = f"kruruto.{userid}.{sessionid_hash}.status"
    user_sessionid = sessionid_hash
  else:
    user_sessions_status_key = f"kruruto.{userid}.{user_sessionid}.status"

  
  
  print('user_session',user_sessionid)
  print("sessionid_hash",sessionid_hash)

  #check session_status ทำไปถึงข้อไหนแล้ว "kruruto.{userid}.{sessionid}.status"
  session_status = get_redis_data(user_sessions_status_key)
  print("session_status-1",user_sessions_status_key,session_status)
  #if session_status == None - > session_status=1, else session_status = session_status+1
  
  if session_status == None:
    # session_status = "1"
    add_redis_data(user_sessions_status_key, "1")
    
  else:
    session_status = int(session_status) + 1
    add_redis_data(user_sessions_status_key, str(session_status))
    print("session_status-N",session_status)
    
  session_status = get_redis_data(user_sessions_status_key)

  print("session_status-X",user_sessions_status_key,session_status)

    
  flex_question = await flex_get_data(title, session_status)
  flex_question = "___TEMPLATE___" + flex_question
  print(flex_question)
  
  return (flex_question)
 

#เรากําลังจะทําตารางคะแนนของนัดเรียนทั้งหมดที่เข้าเรียน เป็นคะแนนรวม
@app.get("/user/get/line/check_score")
async def get_user_score(title: str):
    
    n = get_redis_data(f"kuruto.userid.check")
    userid_list = ""
    for i in range(1, int(n)):
        userid_all = get_redis_data(f"kuruto.userid.{i}")
        user_totalscore = get_redis_data(f"kruruto.top.{userid_all}.{title}.score")
        user_totalscore = int(user_totalscore)
        userid_list = userid_list + f"{user_totalscore},"
        
        
    sorted_numbers = sorted(userid_list, reverse=True)
    return PlainTextResponse(sorted_numbers)
    
    
  

@app.get("/total/score")
async def get_total_score(userid: str,title:str):
    user_sessionid = get_redis_data(f"kruruto.{userid}.sessionid") 

    total_score = 0
    scores = []

    for i in range(1, 19):
        score = get_redis_data(f"kruruto.{userid}.{user_sessionid}.{i}.score")
        if score is not None:
            scores.append(int(score))
            total_score += int(score)  
    return (total_score)
  
  
  
@app.get("/feedback/user")
async def get_feedback(userId: str,feedback: str,status: str):
    if status == "reportproblem":
      add_redis_data(f'{userId}.แจ้งปัญหา', feedback)
    elif status == "reportsuggestion":
      add_redis_data(f'{userId}.ข้อเสนอแนะ', feedback)
    return PlainTextResponse("ok")
  


@app.get("/prenious_user_message")
async def get_user_message(userId: str, message: str):
  # รับค่าเก่ามาก่อน
  pre_message = get_redis_data(f'{userId}.message')
  before_title = get_redis_data(f'{userId}.message.title')
  if before_title == None:
    before_title = ""
  if pre_message == None:
    pre_message = ""
  prompt = f"""
  character:
  ครูเป็ยครูดาราศาสตร์ มีความเชี่ยวชาญในด้านดาราศาสตร์และฟิสิกส์
  ช่วยตอบคำถามของนักเรียนที่มีความรู้พื้นฐานในระดับมัธยมศึกษาตอนต้น
  นักเรียนถามคำถามเกี่ยวกับดาราศาสตร์และฟิสิกส์
  
  previous message:
  ให้ตอบคำถามตามคําถามก่อนหน้าของนักเรียนคือ
  {pre_message}
  
  check similar title:
  หัวข้อที่นักเรียนถามคือ
  {before_title}
  ให้ตรวจสอบว่า ข้อความนี้มีความคล้ายคลึงกับข้อความก่อนหน้าหรือไม่
  ถ้ามีให้ตอบว่า "yes" ถ้าไม่มีให้ตอบว่า "no"
  
  ตอบทั้งหมดในในรูปแบบ json object(message,similar)

  
  

  """    

  
        
  answer = await call_naja(prompt, message,temperature=0.5)
  try:
        return_answer = answer.split("```json")[1].split("```")[0]
        return_answer = json.loads(return_answer)
  except (IndexError, json.JSONDecodeError) as e:
        return PlainTextResponse("ไม่สามารถวิเคราะห์ผลลัพธ์ได้", status_code=500)

  new_message_finall = return_answer["message"]
  similar = return_answer["similar"]
  pre_message = f"{pre_message} {message} {new_message_finall}"


  threading.Thread(target=summary_history, args=(userId, pre_message, similar)).start()

  return PlainTextResponse(f"คําตอบคือ {new_message_finall} ข้อความเก่า{pre_message}")


@app.get("/prenious_user_message/summary_history")
def summary_history(userId: str, pre_message: str, similar: str):
  try:
    if similar == "yes":
      history = summary_history_before(userId, pre_message)
      add_redis_data(f'{userId}.status',1)
    else:
      add_redis_data(f'{userId}.message', "")
      add_redis_data(f'{userId}.status', 0)
  except Exception as e:
    print("Error in summary_history:", str(e))
    add_redis_data(f'{userId}.status', -1)
    return PlainTextResponse("Error in summary_history", status_code=500)
    
  
@app.get("/prenious_user_message/summary_history/before")
async def summary_history_before(userId: str, pre_message: str):
  summary_prompt = f""" 
    คุณเป็นนักวิเคราะห์ที่ช่วยปรับปรุง ข้อความนี้ นี้ให้มี token น้อยกว่าเดิม โดยยังคงเนื้อหาและใจความเดิม แต่ให้กระชับกว่าเดิม
    ตามข้อความนี้ {pre_message} 
    
    และจะสรุปเป็น title เนื้อหาสั้นๆ ว่าเป็นเรื่องอะไร
    และให้แสดงเป็น JSON object
    {
      "title": "ชื่อเรื่อง",
      "content": "เนื้อหา"
    }
    """
  summary_history = await call_naja(summary_prompt, message="ย่อให้ฉันหน่อย",temperature=0.3)
  #ดึงข้อมูลจาก  summary_history title และ content
  summary_history = json.loads(summary_history)
  title = summary_history["title"]
  content = summary_history["content"]
  #เก็บข้อมูลใน redis
  add_redis_data(f'{userId}.message', content)
  add_redis_data(f'{userId}.message.title', title)
  return PlainTextResponse(summary_history)   
  

  
    
@app.get("/getuserprofile")
async def get_userprofile_messageapi(userId:str):
  profile_endpoint = f'https://api.line.me/v2/bot/profile/{userId}'
  
  
  headers = {"Authorization": "Bearer oCIlITMJHbmNR2SkNJ5bDQO08P4qsqWau+mqLmVcXMEd/L9BWv9hORFWic6qU+V4s+3pPaJJ7WVPTfvRIV/rq9KDn+wgFDsI75fKZ0trhkRtK3Yv3aBsllFKmGaDoIdGURuRbNmy2wk6ME7UQjhVKQdB04t89/1O/w1cDnyilFU="}
  
  result = requests.get(profile_endpoint,headers=headers)
  results = result.json()
  
  name = results["displayName"]
  print(name)
  picture = results["pictureUrl"]
  print(picture)
  userid = results["userId"]
  print(userId)
  add_redis_data(f'kruruto.{userid}.name', name) 
  add_redis_data(f'krututo.{userid}.picture', picture)
  found = False
  for n in range(1, 31):
      existing_userid = get_redis_data(f"kruruto.userid.{n}")
      if existing_userid == userId:
          found = True
          break
  if not found:
      for n in range(1, 31):
          existing_userid = get_redis_data(f"kruruto.userid.{n}")
          if existing_userid is None:
              add_redis_data(f"kruruto.userid.{n}", userId)
              break




@app.get("/image/scan/kruruto")
async def scan_image_kruruto(url:str,userid:str):
  image = Image.open(requests.get(url, stream=True).raw)  
  image.save("label.png")
  text = pytesseract.image_to_string(Image.open("label.png"), lang="tha+eng")
  # prompt = """
  #           คุณคือผู้เชี่ยวชาญเกี่ยวกับการปรับแต่งข้อความคุณจะสามารถทําให้ข้อความที่ขาดหายไป เติมแต่งให้สมบูรน์และเนื้อหายังเหมือนเดิมไม่ต่างจากข้อความเก่า

  #             """
  # answer = await call_naja(prompt,temperature=0.3,user_input=text)
  # answer = answer.split("```json")[1].split("```")[0]
  # answer = json.loads(answer)
  # source = f"""{answer}
  # """

  # end_point = "https://llook.abdul.in.th/docchat/api/v1/core/index-text"

  # data = {
  #   "project_id":"kruruto",
  #   "title":f"{userid}",
  #   "source":source
  # }

  # headers = {"token":"interndev"}

  # res = requests.post(end_point,json=data,headers=headers)
  # res
  return text 
  # return PlainTextResponse("สามารถถามเกี่ยวกับเนื้อหาที่คุณเรียนมาได้เลยนะครับ")

@app.get("/ask/llook/user")
async def ask_llook_user(title:str,level:int,kname:str):
  global prompt_question_1, prompt_question_2, prompt_question_3, prompt_question_4,  prompt_question_5
  if level == 1:
      guidelines = prompt_question_1
  elif level == 2:
      guidelines = prompt_question_2
  elif level == 3:
      guidelines = prompt_question_3
  elif level == 4:
      guidelines = prompt_question_4
  elif level == 5:
      guidelines = prompt_question_5
  else:
      raise ValueError("Level not found")
  guidelines = guidelines.replace("__title__", title)
  end_point = "https://llook.abdul.in.th/docchat/api/v1/core/chat"
  kru = teacher_list.get(kname)
  params = {
    "session_id":"xxx",
    "project_id":"kruruto",
    "user_message":f"สอนเรื่อง {title} ให้ฉันหน่อย",
    "title":f"{title}",
    "temperature": 0.4,
    "persona": f"""คุณต้องเริ่มต้นสนทนาว่า "สวัสดีครับนักเรียน" และอุปนิสัยของคุณคือ  {kru['prompt']} และนี่คือแนวทางของคุณ {guidelines}
        """
  }
  headers = {"token":"interndev"}
  res = requests.post(end_point,data=params,headers=headers)
  result = res.json()['content']
  return result

@app.get("/ask/gemma/user")
async def ask_gemma_user(user_input:str,title:str,level:int,kname:str):
  global prompt_question_1, prompt_question_2, prompt_question_3, prompt_question_4,  prompt_question_5
  if level == 1:
      guidelines = prompt_question_1
  elif level == 2:
      guidelines = prompt_question_2
  elif level == 3:
      guidelines = prompt_question_3
  elif level == 4:
      guidelines = prompt_question_4
  elif level == 5:
      guidelines = prompt_question_5
  else:
      raise ValueError("Level not found")
  kru = teacher_list.get(kname)
  prompt = f"""
  คุณคือ {kru['prompt']} และนี่คือแนวทางของคุณ {guidelines}
  ให้ตอบคําถามนักเรียนตามหัวข้อที่นักเรียนถามคือ {title}
  """
  answer = await call_naja(prompt,user_input,temperature=0.4)
  return answer

@app.get("/useranswer")
async def user_answer(userid: str, title: str, user_answer: int,kname: str):
  
  
  user_status = get_redis_data(f"kruruto.{userid}.status")
  user_correct_status = get_redis_data(f"kruruto.{userid}.correct.status")
  
  if user_status is None:
    user_status = "1"
  if user_status == "6":
    return PlainTextResponse("คุณได้ตอบคำถามครบแล้ว")
  
  
  if user_correct_status is None:
    user_correct_status = "1"
  if user_correct_status == "2":
    user_status = int(user_status) + 1
    add_redis_data(f"kruruto.{userid}.status", int(user_status))
    add_redis_data(f"kruruto.{userid}.correct.status", 0)
    answer = user_answer(userid, title, user_answer, kname)
    return PlainTextResponse(answer)
    
  
  
  if user_answer == 1:
    user_correct_status = int(user_correct_status) + 1
    add_redis_data(f"kruruto.{userid}.correct.status", int(user_correct_status))
    answer = await ask_llook_user(title, int(user_status), kname)
    return PlainTextResponse(answer)
  elif user_answer == 0:
    add_redis_data(f"kruruto.{userid}.correct.status", 0)
    answer = await ask_llook_user(title, int(user_status), kname)
    return PlainTextResponse(answer)
  else:
    return PlainTextResponse("Invalid user answer", status_code=400)
  
  
  
  
