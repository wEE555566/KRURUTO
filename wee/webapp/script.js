let userProfile = {};
let statuss = "";

async function get_data_line() {
  await liff.init({ liffId: "2007279692-e5gRZy84" });
  if (!liff.isLoggedIn()) {
    liff.login();
  } else {
    userProfile = await liff.getProfile();
  }
}

get_data_line();

function showInput(type) {
  inputproblem = document.getElementById("inputproblem");
  inputsuggestion = document.getElementById("inputsuggestion");
  sendButton = document.getElementById("send");
  reportproblem = document.getElementById("reportproblem");
  reportsuggestion = document.getElementById("reportsuggestion");

  if (type === "problem") {
    inputproblem.style.display = "block";
    inputsuggestion.style.display = "none";
    reportproblem.style.backgroundColor = "#74b8eb";
    reportsuggestion.style.backgroundColor = "#D1E5F4";
    reportproblem.style.color = "#FFFFFF";
    reportsuggestion.style.color = "#000000";
    inputsuggestion.value = "";
    reportproblem.classList.add("active");
    reportsuggestion.classList.remove("active");
  } else if (type === "suggestion") {
    inputproblem.style.display = "none";
    inputsuggestion.style.display = "block";
    reportproblem.style.backgroundColor = "#D1E5F4";
    reportsuggestion.style.backgroundColor = "#74b8eb";
    reportproblem.style.color = "#000000";
    reportsuggestion.style.color = "#FFFFFF";
    inputproblem.value = "";
    reportsuggestion.classList.add("active");
    reportproblem.classList.remove("active");
  }

  sendButton.style.display = "block";
}

document.getElementById("reportproblem").addEventListener("click", function () {
  statuss = "reportproblem";
});

document.getElementById("reportsuggestion").addEventListener("click", function () {
  statuss = "reportsuggestion";
});

document
  .getElementById("feedback")
  .addEventListener("submit", async function (event) {
    event.preventDefault();

    const inputproblem = document.getElementById("inputproblem");
    const inputsuggestion = document.getElementById("inputsuggestion");

    let message = "";
    if (inputproblem.style.display === "block") {
      if (inputproblem.value.trim() === "") {
        alert("อย่าลืมแจ้งปัญหาก่อนส่งนะครับ ^^");
        return;
      }
      message = inputproblem.value.trim();
    } else if (inputsuggestion.style.display === "block") {
      if (inputsuggestion.value.trim() === "") {
        alert("อย่าลืมใส่ข้อเสนอแนะก่อนส่งนะครับ ^^");
        return;
      }
      message = inputsuggestion.value.trim();
    }

    try {
      
      await axios.get("https://dev.abdul.in.th/wee/api/v1/feedback/user", {
        params: {
          userId: userProfile.userId,
          feedback: message,
          status: statuss, 
        },
      });

      alert("บันทึกข้อมูลสำเร็จ !");
      window.location.href = "index.html";
    } catch (error) {
      console.error(error);
      alert("เกิดข้อผิดพลาดในการส่งข้อมูล");
    }
  });
