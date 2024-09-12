
// this jss isn't using

// const constraints = {
//     video: {
//         facingMode: 'environment' // 使用後置相機
//     }
// };

// async function init() {
//     try {
//         const stream = await navigator.mediaDevices.getUserMedia(constraints);
//         const video = document.getElementById('video');
//         video.srcObject = stream;
//     } catch (err) {
//         console.error('錯誤: ' + err);
//         alert('無法訪問相機: ' + err.message);
//     }
// }

// async function captureAndProcessImage() {
//     const video = document.getElementById('video');
//     const canvas = document.createElement('canvas');
//     const context = canvas.getContext('2d');
//     canvas.width = video.videoWidth;
//     canvas.height = video.videoHeight;
//     context.drawImage(video, 0, 0, canvas.width, canvas.height);
//     const dataURL = canvas.toDataURL('image/png');

//     console.log("Captured image DataURL:", dataURL);  // 添加这一行来检查 DataURL

//     // 發送圖像數據進行處理
//     const response = await fetch('/process', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json'
//         },
//         body: JSON.stringify({ image: dataURL })
//     });

//     const result = await response.json();
//     const processed = document.getElementById('processed');
//     if (processed) {
//         processed.src = 'data:image/png;base64,' + result.processed_image;
//     } else {
//         console.error("Element with id 'processed' not found.");
//     }
// }

// document.getElementById('snap').addEventListener('click', captureAndProcessImage);

// window.onload = init;
