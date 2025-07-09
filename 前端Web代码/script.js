/* ReadMe */
/* 本代码是Web前端DashBoard的JS部分 */
/*后端依赖API：1.https://mqttapi.silence.wiki/api/status
              2.https://mqttapi.silence.wiki/api/control
              3.https://chatapi.silence.wiki/rkllm_chat
              4.https://whisperapi.silence.wiki/whisper*/
/* API部分由各个Flask管理 */        
/* ReadMe */

// 权限检查
document.addEventListener('DOMContentLoaded', async function() {
  const role = localStorage.getItem('userRole');
  if (role !== 'user') {  
    alert('您没有权限访问此页面!');
    window.location.href = 'index.html';
    return;
  }
});

// 全局函数：切换侧边栏标签页
window.switchTab = function (tab) {
  // 切换按钮激活状态
  document.querySelectorAll('.sidebar button').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });

  // 隐藏所有模块
  document.querySelectorAll('.module').forEach(mod => {
    mod.style.display = 'none';
  });

  // 显示目标模块
  const activeModule = document.getElementById(`${tab}-module`);
  if (activeModule) {
    if (tab === 'mqtt') {
      // MQTT模块
      activeModule.style.display = '';
    } else {
      // 其他模块
      activeModule.style.display = 'block';
    }
  }

  // YOLO视频流切换
  if (tab === 'yolo') {
    window.startVideoStream();
  } else {
    window.stopVideoStream();
  }
};


(function () {
  // 传感器和设备数据结构
  const sensors = {
    temperature: { name: "温度", unit: "℃", value: "--" },
    humidity: { name: "湿度", unit: "%", value: "--" },
    pressure: { name: "大气压强", unit: "hPa", value: "--" },
    co2: { name: "CO2浓度", unit: "ppm", value: "--" },
    tvoc: { name: "TVOC浓度", unit: "ppb", value: "--" },
    light: { name: "光照度", unit: "lux", value: "--" },
    tof: { name: "距离", unit: "mm", value: "--" },
    voltage: { name: "电池电压", unit: "V", value: "--" },
    current: { name: "电池电流", unit: "A", value: "--" },
    power: { name: "电池功率", unit: "W", value: "--" },
    energy_wh: { name: "累计电量", unit: "Wh", value: "--" },
    soc: { name: "电池电量百分比", unit: "%" }
  };

  const devices = {
    B401: { name: "B401灯光", state: "off" },
    B402: { name: "B402灯光", state: "off" },
    B403: { name: "B403灯光", state: "off" },
    B404: { name: "B404灯光", state: "off" },
    B405: { name: "B405灯光", state: "off" },
    Door: { name: "Door", state: "off" },
    Fan: { name: "风扇", speed: 0 }  // 继电器改成风扇，初始转速0%
  };

  const gridContainer = document.getElementById("grid-container");

  // 生成传感器卡片
  function createSensorCard(key) {
    const sensor = sensors[key];
    const card = document.createElement("div");
    card.className = "card sensor-card";
    card.id = `sensor-${key}`;
    card.innerHTML = `
      <div class="title">${sensor.name}</div>
      <div><span class="sensor-value" id="value-${key}">${sensor.value}</span><span class="unit">${sensor.unit}</span></div>
    `;
    return card;
  }

  // 生成设备卡片
  function createDeviceCard(key) {
    const device = devices[key];
    const card = document.createElement("div");
    card.className = "card device-card";
    card.id = `device-${key}`;

    updateDeviceCardClass(card, device.state);

    const titleDiv = document.createElement("div");
    titleDiv.className = "title";
    titleDiv.textContent = device.name;

    card.appendChild(titleDiv);

    if (key === "Fan") {
      let isFanStatusUpdating = false;

      // Fan
      const fanImg = document.createElement("img");
      fanImg.src = "fan.png";
      fanImg.alt = "风扇";
      fanImg.id = "fan-image";
      fanImg.style.width = "60px";
      fanImg.style.height = "60px";
      fanImg.style.display = "block";
      fanImg.style.margin = "0 auto 10px auto";
      fanImg.style.transition = "transform 0.2s linear";

      // Slider
      const sliderContainer = document.createElement("div");
      sliderContainer.className = "fan-speed-control";
      sliderContainer.style.textAlign = "center";

      const slider = document.createElement("input");
      slider.type = "range";
      slider.min = "0";
      slider.max = "100";
      slider.value = device.speed || 0;
      slider.id = "fan-speed-slider";

      const speedLabel = document.createElement("span");
      speedLabel.id = "fan-speed-label";
      speedLabel.textContent = `${slider.value}%`;
      speedLabel.style.marginLeft = "10px";
      speedLabel.style.fontWeight = "bold";

      sliderContainer.appendChild(slider);
      sliderContainer.appendChild(speedLabel);

      card.appendChild(fanImg);
      card.appendChild(sliderContainer);

      // Fan_animation
      window.updateFanUI = function (speed) {
        isFanStatusUpdating = true;
        slider.value = speed;
        speedLabel.textContent = speed + "%";

        if (speed > 0) {
          const minDuration = 5;
          const maxDuration = 0.6;
          const duration = minDuration - (speed / 100) * (minDuration - maxDuration);
          fanImg.style.setProperty("--spin-duration", duration + "s");
          fanImg.style.animationPlayState = "running";
        } else {
          fanImg.style.animationPlayState = "paused";
        }

        isFanStatusUpdating = false;
      };

      //UI_init
      updateFanUI(device.speed || 0);

      //Slider_progress
      slider.addEventListener("input", () => {
        if (isFanStatusUpdating) return;

        const speed = Number(slider.value);
        speedLabel.textContent = speed + "%";

        if (speed > 0) {
          const minDuration = 5;
          const maxDuration = 0.6;
          const duration = minDuration - (speed / 100) * (minDuration - maxDuration);
          fanImg.style.setProperty("--spin-duration", duration + "s");
          fanImg.style.animationPlayState = "running";
        } else {
          fanImg.style.animationPlayState = "paused";
        }

        sendControl("Fan", speed);
        devices.Fan.speed = speed;
      });
    } else {
      // 普通设备控制按钮
      const controlsDiv = document.createElement("div");
      controlsDiv.className = "device-controls";
      controlsDiv.innerHTML = `
        <button class="btn-on" data-device="${key}" data-command="ON">开</button>
        <button class="btn-off" data-device="${key}" data-command="OFF">关</button>
      `;

      card.appendChild(controlsDiv);

      controlsDiv.querySelectorAll("button").forEach(btn => {
        btn.addEventListener("click", () => {
          sendControl(btn.dataset.device, btn.dataset.command);
        });
      });
    }

    return card;
  }

  // 更新设备卡片样式
  function updateDeviceCardClass(card, state) {
    card.classList.remove("on", "b-light-on", "b-dark-off", "b-door-on", "b-door-off");

    const id = card.id; // e.g. device-Door
    const key = id.replace("device-", "");

    if (key === "Door") {
      if (state === "on") {
        card.classList.add("on", "b-door-on");
      } else {
        card.classList.add("b-door-off");
      }
    } else if (["B401", "B402", "B403", "B404", "B405"].includes(key)) {
      if (state === "on") {
        card.classList.add("on", "b-light-on");
      } else {
        card.classList.add("b-dark-off");
      }
    } else {
      if (state === "on") {
        card.classList.add("on");
      }
    }
  }

  // 初始化所有卡片
  function initCards() {
    gridContainer.innerHTML = "";
    Object.keys(sensors).forEach(key => {
      gridContainer.appendChild(createSensorCard(key));
    });
    Object.keys(devices).forEach(key => {
      gridContainer.appendChild(createDeviceCard(key));
    });
  }
  initCards();

  // API获取设备状态
  async function fetchStatus() {
    try {
      const resp = await fetch('https://mqttapi.silence.wiki/api/status');
      if (!resp.ok) throw new Error("状态获取失败");
      const data = await resp.json();

      // 更新设备状态
      for (const key in data.devices) {
        if (devices[key]) {
          if (key === "Fan") {
            // Fan 是数字，直接赋值
            const speed = data.devices[key];
            devices[key].speed = data.devices[key];
            if (typeof updateFanUI === "function") updateFanUI(speed);
            // 你可以更新对应显示，比如：
            const valElem = document.getElementById(`value-${key}`);
            if (valElem) valElem.textContent = devices[key].speed + "%";
          } else {
            // 其他设备是字符串，做小写处理
            devices[key].state = data.devices[key].toLowerCase();
            const card = document.getElementById(`device-${key}`);
            if (card) updateDeviceCardClass(card, devices[key].state);
          }
        }
      }

      // 更新传感器值
      for (const key in data.sensors) {
        if (sensors[key]) {
          sensors[key].value = data.sensors[key];
          const valElem = document.getElementById(`value-${key}`);
          if (valElem) valElem.textContent = sensors[key].value;
        }
      }
    } catch (e) {
      console.error("获取状态失败:", e);
    }
  }

  // 发送控制命令
  async function sendControl(device, command) {
    try {
      const resp = await fetch('https://mqttapi.silence.wiki/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device, command })
      });

      const data = await resp.json();
      if (data.status === 'success') {
        console.log(`控制命令发送成功: ${device} -> ${command}`);
        fetchStatus(); // 控制成功后刷新状态
      } else {
        console.error('控制命令失败', data);
      }
    } catch (e) {
      console.error('控制请求异常', e);
    }
  }

  // 启动轮询状态更新
  setInterval(fetchStatus, 1000);
  fetchStatus();

  // YOLO视频流播放
  let webrtcPC = null;

  window.startVideoStream = function () {
    const container = document.getElementById("webrtcPlayerContainer");
    if (!container) return;
    container.innerHTML = `
      <div id="loadingOverlay">
        <div id="loadingSpinner"></div>
        <div id="loadingText">视频加载中...</div>
      </div>
    `;

    const video = document.createElement("video");
    video.autoplay = true;
    video.playsInline = true;
    video.controls = true;
    video.muted = true;
    video.style.width = "100%";
    video.style.height = "100%";
    video.style.backgroundColor = "#000";
    container.appendChild(video);

    const hideLoading = () => {
      const overlay = document.getElementById("loadingOverlay");
      if (overlay) overlay.style.display = "none";
      video.classList.add('playing');
    };

    video.onplaying = hideLoading;

    webrtcPC = new RTCPeerConnection({ iceServers: [{ urls: ['stun:stun.l.google.com:19302'] }] });

    webrtcPC.ontrack = event => {
      const stream = event.streams[0];
      if (stream) {
        video.srcObject = stream;
        video.onloadeddata = () => video.play().then(hideLoading).catch(console.warn);
      }
    };

    webrtcPC.addTransceiver('video', { direction: 'recvonly' });

    webrtcPC.createOffer()
      .then(offer => webrtcPC.setLocalDescription(offer))
      .then(() => fetch('https://yoloapi.silence.wiki/mystream/whep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/sdp' },
        body: webrtcPC.localDescription.sdp
      }))
      .then(res => {
        if (!res.ok) throw new Error('WHEP SDP answer 获取失败，状态码: ' + res.status);
        return res.text();
      })
      .then(answerSdp => webrtcPC.setRemoteDescription({ type: 'answer', sdp: answerSdp }))
      .then(() => console.log('WHEP WebRTC 连接建立完成'))
      .catch(err => {
        console.error('WHEP WebRTC连接错误:', err);
        alert('WHEP 视频播放失败，请检查控制台错误');
        window.stopVideoStream();
      });
  };

  window.stopVideoStream = function () {
    if (webrtcPC) {
      webrtcPC.close();
      webrtcPC = null;
    }
    const container = document.getElementById("webrtcPlayerContainer");
    if (container) container.innerHTML = "";
  };

  // 显示当前时间
  function updateCurrentTime() {
    const now = new Date();
    const hh = now.getHours().toString().padStart(2, '0');
    const mm = now.getMinutes().toString().padStart(2, '0');
    const ss = now.getSeconds().toString().padStart(2, '0');
    const clock = document.getElementById('current-time');
    if (clock) clock.textContent = `${hh}:${mm}:${ss}`;
  }
  setInterval(updateCurrentTime, 1000);
  
    // 禁用发送按钮
  function disableSendButton() {
    const sendBtn = document.getElementById("send-btn");
    if (sendBtn) {
      sendBtn.disabled = true;
      sendBtn.classList.add("disabled");
    }
  }

  // 启用发送按钮
  function enableSendButton() {
    const sendBtn = document.getElementById("send-btn");
    if (sendBtn) {
      sendBtn.disabled = false;
      sendBtn.classList.remove("disabled");
    }
  }


  // 聊天模块相关变量
  const chatLog = document.getElementById("chat-log");
  const inputField = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  const recordBtn = document.getElementById("record-btn");
  sendBtn.disabled = true;
  inputField.addEventListener('input', () => {
  if (inputField.value.trim() === '') {
    sendBtn.disabled = true;
  } else {
    sendBtn.disabled = false;
  }
  });

  let mediaRecorder = null;
  let audioChunks = [];

  // 录音按钮事件
  recordBtn.onclick = async () => {
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = event => audioChunks.push(event.data);

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
          const formData = new FormData();
          formData.append("file", audioBlob, "record.wav");

          try {
            const response = await fetch("https://whisperapi.silence.wiki/whisper", { method: "POST", body: formData });
            const result = await response.json();
            inputField.value = result.transcript || "识别失败";
            
            // 识别结果填入后启用发送按钮
            sendBtn.disabled = false;  // 启用发送按钮
          } catch (err) {
            inputField.value = "识别请求失败";
            console.error(err);
          }
        };

        mediaRecorder.start();
        recordBtn.classList.add('recording');
        recordBtn.disabled = false;  // 根据需求禁用或启用
        recordBtn.textContent = "停止录音";
      } catch (err) {
        alert("获取麦克风权限失败");
        console.error(err);
      }
    } else {
      mediaRecorder.stop();
      recordBtn.classList.remove('recording');
      recordBtn.disabled = false;
      recordBtn.textContent = "录音";
    }
  };

  async function controlDevices(devices, command, action, userText) {
    disableSendButton();
    const results = [];

    const promises = devices.map(device =>
      sendControl(device, command)
        .then(() => results.push(`${device}灯光已${action === '打开' ? '打开' : '关闭'}`))
        .catch(() => results.push(`${device}灯光控制失败`))
    );

    try {
      await Promise.all(promises);
      appendMessage("user", userText);
      appendMessage("ai", results.join("，"));
    } catch (e) {
      console.error("批量控制失败:", e);
      appendMessage("user", userText);
      appendMessage("ai", "部分灯光控制失败，请稍后重试。");
    } finally {
      enableSendButton();
      inputField.value = "";
    }
  }

  // 发送按钮事件，只定义一次
  sendBtn.onclick = async () => {
    const text = inputField.value.trim();
    if (!text) return;
    if (/实验室状况如何|实验室情况怎么样|实验室环境怎样/i.test(text)) {
      let sensorStatus = Object.entries(sensors).map(([key, sensor]) => {
        let val = sensor.value === "--" ? "无数据" : sensor.value + (sensor.unit || "");
        return `${sensor.name}：${val}`;
      }).join("，");

      let deviceStatus = Object.entries(devices).map(([key, device]) => {
        if (key === "Fan") {
          return `${device.name}转速：${device.speed}%`;
        } else {
          return `${device.name}状态：${device.state === "on" ? "开启" : "关闭"}`;
        }
      }).join("，");

      const reply = `当前实验室传感器状态如下：${sensorStatus}。设备状态如下：${deviceStatus}。`;

      appendMessage("user", text);
      appendMessage("ai", reply);
      inputField.value = "";
      enableSendButton();
      return; // 这里结束，不再走AI接口
    }
    const fanSpeedText = text.match(/风扇(?:转速)?(?:调到)?(\d{1,3})%?/);
    const fanAdjustUp = /(风扇.*调(大|高)(点)?|风扇转速调高(\d{1,2})?%?)/i;
    const fanAdjustDown = /(风扇.*调(小|低)(点)?|风扇转速调低(\d{1,2})?%?)/i;
    const fanTurnOff = /关闭风扇/i;
    const fanTurnOn = /(开启|打开|启动)风扇/i;  

    if (fanTurnOff.test(text)) {
      await sendControl("Fan", 0);
      devices.Fan.speed = 0;
      appendMessage("user", text);
      appendMessage("ai", `风扇已关闭`);
      inputField.value = "";
      enableSendButton();
      return;
    }

    if (fanTurnOn.test(text)) {
      const speed = 50;
      await sendControl("Fan", speed);
      devices.Fan.speed = speed;
      appendMessage("user", text);
      appendMessage("ai", `风扇已开启，当前转速 ${speed}%`);
      inputField.value = "";
      enableSendButton();
      return;
    }

    if (fanSpeedText) {
      let speed = Math.min(100, Math.max(0, parseInt(fanSpeedText[1])));
      await sendControl("Fan", speed);
      devices.Fan.speed = speed;
      appendMessage("user", text);
      appendMessage("ai", `风扇转速已设置为 ${speed}%`);
      inputField.value = "";
      enableSendButton();
      return;
    }

    if (fanAdjustDown.test(text)) {
      const reduceMatch = text.match(/调低(\d{1,2})%?/);
      const reduce = reduceMatch ? parseInt(reduceMatch[1]) : 10;
      let newSpeed = Math.max(0, devices.Fan.speed - reduce);
      await sendControl("Fan", newSpeed);
      devices.Fan.speed = newSpeed;
      appendMessage("user", text);
      appendMessage("ai", `风扇转速已降低至 ${newSpeed}%`);
      inputField.value = "";
      enableSendButton();
      return;
    }

    if (fanAdjustUp.test(text)) {
      const addMatch = text.match(/调高(\d{1,2})%?/);
      const increase = addMatch ? parseInt(addMatch[1]) : 10;
      let newSpeed = Math.min(100, devices.Fan.speed + increase);
      await sendControl("Fan", newSpeed);
      devices.Fan.speed = newSpeed;
      appendMessage("user", text);
      appendMessage("ai", `风扇转速已提高至 ${newSpeed}%`);
      inputField.value = "";
      enableSendButton();
      return;
    }
    // 先支持控制所有灯光
    if (/^(关闭|关闭所有|开启|打开|打开所有)灯光$|^(关闭|关闭所有|开启|打开|打开所有)所有灯光$/i.test(text)) {
      const action = /^(关闭|关闭所有)/i.test(text) ? "关闭" : "打开";
      const command = action === "打开" ? "ON" : "OFF";

      const allDevices = ["B401", "B402", "B403", "B404", "B405"];
      await controlDevices(allDevices, command, action, text);
      return;
    }

    // 用正则匹配所有动作
    const controlRegex = /(打开|关闭|开启)([^\s，,、]+)(灯光?)/gi;
    const matches = [...text.matchAll(controlRegex)];

    if (matches.length > 0) {
      // 设备范围解析函数
      function parseDevices(deviceStr) {
        const devices = [];
        const parts = deviceStr.split(/和|、|,/);
        for (const part of parts) {
          const rangeMatch = part.match(/(B40[1-5])到(B40[1-5])/i);
          if (rangeMatch) {
            const startNum = parseInt(rangeMatch[1].slice(3));
            const endNum = parseInt(rangeMatch[2].slice(3));
            const from = Math.min(startNum, endNum);
            const to = Math.max(startNum, endNum);
            for (let i = from; i <= to; i++) {
              devices.push(`B40${i}`);
            }
          } else {
            const d = part.trim().toUpperCase();
            if (/^B40[1-5]$/.test(d)) devices.push(d);
          }
        }
        return devices;
      }

      let allDevices = [];
      let action = null;

      for (const match of matches) {
        action = match[1] === "开启" ? "打开" : match[1];
        const deviceStr = match[2];
        allDevices = allDevices.concat(parseDevices(deviceStr));
      }
      allDevices = [...new Set(allDevices)]; // 去重

      const command = action === "打开" ? "ON" : "OFF";
      await controlDevices(allDevices, command, action, text);
      return;
    }

    // 非灯光控制，走AI流程
    appendMessage("user", text);
    inputField.value = "";
    await streamAIResponse(text);
  };

  // 添加消息到聊天窗口
  function appendMessage(role, text) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    if (role === "user") {
      const avatar = document.createElement("img");
      avatar.className = "avatar";
      avatar.src = "user.png";
      avatar.alt = "用户头像";
      bubble.textContent = text;
      messageDiv.appendChild(bubble);
      messageDiv.appendChild(avatar);
    } else if (role === "ai") {
      const avatar = document.createElement("img");
      avatar.className = "avatar";
      avatar.src = "ai.png";
      avatar.alt = "AI头像";
      messageDiv.appendChild(avatar);
      bubble.textContent = text;
      messageDiv.appendChild(bubble);
    } else if (role === "thinking") {
      messageDiv.classList.add("thinking");
      bubble.classList.add("thinking");
      bubble.textContent = text;
      messageDiv.appendChild(bubble);
    }

    chatLog.appendChild(messageDiv);
    chatLog.scrollTop = chatLog.scrollHeight;

    return bubble;
  }

  // 流式接收AI回复
  async function streamAIResponse(userText) {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    disableSendButton();
    let fullThinkingText = "";
    let thinkingDone = false;

    const thinkingBubble = appendMessage("thinking", isMobile ? "… 思考中..." : "… AI 正在思考，点击展开查看");
    let answerBubble = null;
    let isThinking = true;
    let expanded = false;
    const sendButton = document.getElementById("send-btn"); 
    const thinkingContainer = thinkingBubble.parentElement;
    thinkingContainer.onclick = () => {
      expanded = !expanded;
      if (expanded) {
        thinkingBubble.classList.add("expanded");
        thinkingBubble.classList.remove("collapsing");
        thinkingBubble.style.maxHeight = "280px";

        thinkingBubble.addEventListener("transitionend", function handleTransitionEnd(e) {
          if (e.propertyName === "max-height") {
            thinkingBubble.style.overflowY = "auto";
            thinkingBubble.removeEventListener("transitionend", handleTransitionEnd);
          }
        });

        if (thinkingDone) {
          thinkingBubble.classList.add("paused");
          thinkingBubble.textContent = isMobile
            ? (fullThinkingText || "（无内容）")
            : (fullThinkingText || "(无思考内容)");
          thinkingBubble.style.opacity = "1";
          thinkingBubble.style.boxShadow =
            "0 0 20px 5px rgba(120,130,180,0.8), inset 0 0 30px 5px rgba(140,150,210,1)";
        } else {
          thinkingBubble.classList.remove("paused");
          thinkingBubble.textContent = isMobile
            ? (fullThinkingText || "… 思考中...")
            : (fullThinkingText || "… AI 正在思考中...");
          thinkingBubble.style.opacity = "0.75";
          thinkingBubble.style.boxShadow =
            "0 0 14px 3px rgba(90,100,140,0.6), inset 0 0 18px 3px rgba(110,120,170,0.8)";
        }
      } else {
        thinkingBubble.classList.remove("expanded");
        thinkingBubble.classList.add("collapsing");
        thinkingBubble.style.maxHeight = "2.4em";
        thinkingBubble.style.overflowY = "hidden";

        if (thinkingDone) {
          thinkingBubble.classList.add("paused");
          thinkingBubble.textContent = isMobile
            ? "… 思考完毕"
            : "… AI 思考完毕，点击展开查看";
          thinkingBubble.style.opacity = "0.65";
          thinkingBubble.style.boxShadow =
            "0 0 8px 2px rgba(80,85,110,0.4), inset 0 0 10px 2px rgba(100,105,130,0.6)";
        } else {
          thinkingBubble.classList.remove("paused");
          thinkingBubble.textContent = isMobile
            ? "… 思考中..."
            : "… AI 正在思考中...";
          thinkingBubble.style.opacity = "0.75";
          thinkingBubble.style.boxShadow =
            "0 0 14px 3px rgba(90,100,140,0.6), inset 0 0 18px 3px rgba(110,120,170,0.8)";
        }

        const onTransitionEnd = (e) => {
          if (e.propertyName === "max-height") {
            thinkingBubble.classList.remove("collapsing");
            thinkingBubble.style.maxHeight = "";
            thinkingBubble.removeEventListener("transitionend", onTransitionEnd);
          }
        };
        thinkingBubble.addEventListener("transitionend", onTransitionEnd);
      }
    };



    try {
      const response = await fetch("https://chatapi.silence.wiki/rkllm_chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [{ role: "user", content: userText }], stream: true }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let boundary;
        while ((boundary = buffer.indexOf("\n\n")) !== -1) {
          const chunk = buffer.slice(0, boundary).trim();
          buffer = buffer.slice(boundary + 2);

          try {
            const parsed = JSON.parse(chunk);
            const delta = parsed.choices?.[0]?.delta;
            if (delta?.content) {
              let content = delta.content;

              if (isThinking) {
                const thinkEndIndex = content.indexOf("</think>");
                if (thinkEndIndex !== -1) {
                  fullThinkingText += content.substring(0, thinkEndIndex);
                  thinkingBubble.textContent = isMobile
                    ? "… 思考完毕"
                    : "… AI 思考完毕，点击展开查看";
                  thinkingDone = true;

                  const answerText = content.substring(thinkEndIndex + 8);
                  answerBubble = appendMessage("ai", answerText);

                  isThinking = false;
                  enableSendButton();

                  thinkingBubble.classList.add("paused");
                  thinkingBubble.style.opacity = "0.65";
                  thinkingBubble.style.boxShadow =
                    "0 0 8px 2px rgba(80,85,110,0.4), inset 0 0 10px 2px rgba(100,105,130,0.6)";
                } else {
                  fullThinkingText += content;
                  if (expanded) {
                    thinkingBubble.textContent = fullThinkingText;
                  }
                }
              } else {
                if (answerBubble) answerBubble.textContent += content.trimStart();
              }

              chatLog.scrollTop = chatLog.scrollHeight;
            }
          } catch (e) {
            console.warn("解析流式数据失败：", chunk, e);
            enableSendButton();
          }
        }
      }
    } catch (e) {
      console.error("AI回复请求失败:", e);
      thinkingBubble.textContent = "AI回复失败，请重试。";
      enableSendButton();
    }
  }
})();
