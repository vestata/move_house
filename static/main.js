document.getElementById('volumeForm').addEventListener('submit', function(event) {
    event.preventDefault();
    // Add your form handling logic here
});

document.getElementById('aiForm').addEventListener('submit', function(event) {
    event.preventDefault();
    // Add your form handling logic here
});

document.getElementById('clearButton').addEventListener('click', clearForms);

function sendToLineBot(data) {
    fetch('YOUR_LINE_BOT_API_ENDPOINT', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

document.getElementById('upload1').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const imageData = e.target.result.split(',')[1];
            fetch('{{ url_for("process") }}', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ image: `data:image/jpeg;base64,${imageData}` })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Server response:', data);

                if (data.error) {
                    alert('圖像處理失敗');
                } else {
                    // 更新箱子數量
                    document.getElementById('ai-large').value = data.large;
                    document.getElementById('ai-medium').value = data.medium;
                    document.getElementById('ai-small').value = data.small;
                    document.getElementById('ai-car-estimate').value = data.car;
                    // 保存車的數量到 sessionStorage
                    sessionStorage.setItem('ai-car-estimate', data.car || 0);

                    // 更新顯示車的數量
                    document.getElementById('ai-car-estimate').value = sessionStorage.getItem('ai-car-estimate');

                    // 儲存數據到 localStorage
                    localStorage.setItem('ai-large', data.large);
                    localStorage.setItem('ai-medium', data.medium);
                    localStorage.setItem('ai-small', data.small);
                    localStorage.setItem('ai-car-estimate', data.car || 0);

                    // 返回主頁
                    window.location.href = '{{ url_for("home") }}';
                }
            })
            .catch(error => {
                console.error('Error fetching data:', error);
            });

        };
        reader.readAsDataURL(file);
    } else {
        console.error('No file selected');
    }
});

window.onload = function() {

    if (!shouldPreserveStorage()) {
        clearLocalStorage();
    } else {
        removePreserveParameter();
    }

    function loadFromLocalStorage(key, elementId) {
        let value = localStorage.getItem(key);
        if (value === null || value === "") {
            value = "0";
        }
        document.getElementById(elementId).value = value;
        return value;
    }

    const large = loadFromLocalStorage('ai-large', 'ai-large');
    const medium = loadFromLocalStorage('ai-medium', 'ai-medium');
    const small = loadFromLocalStorage('ai-small', 'ai-small');
    const car = loadFromLocalStorage('ai-car-estimate', 'ai-car-estimate');
    // const car = sessionStorage.getItem('ai-car-estimate') || '0.5';
    // document.getElementById('ai-car-estimate').value = car;

    console.log('Loaded from sessionStorage:', {
        large: localStorage.getItem('ai-large'),
        medium: localStorage.getItem('ai-medium'),
        small: localStorage.getItem('ai-small'),
        car: localStorage.getItem('ai-car-estimate')
    });
};

function clearLocalStorage() {
    localStorage.removeItem('ai-large');
    localStorage.removeItem('ai-medium');
    localStorage.removeItem('ai-small');
    localStorage.removeItem('ai-car-estimate');
    sessionStorage.removeItem('ai-car-estimate');
    console.log('LocalStorage and sessionStorage cleared');
}

function shouldPreserveStorage() {
    const params = new URLSearchParams(window.location.search);
    const preserve = params.has('preserve');
    console.log('Preserve parameter exists:', preserve);
    return preserve;
}

function removePreserveParameter() {
    const url = new URL(window.location);
    url.searchParams.delete('preserve');
    window.history.replaceState({}, document.title, url.toString());
    console.log('Preserve parameter removed from URL');
}

function clearForms() {
    document.getElementById('length').value = '';
    document.getElementById('width').value = '';
    document.getElementById('height').value = '';
    document.getElementById('large').value = '';
    document.getElementById('medium').value = '';
    document.getElementById('small').value = '';
    document.getElementById('car-estimate').value = '';

    document.getElementById('ai-large').value = '';
    document.getElementById('ai-medium').value = '';
    document.getElementById('ai-small').value = '';
    document.getElementById('hang-box').value = '';
    document.getElementById('ai-car-estimate').value = '';

    clearLocalStorage();
    console.log('Forms cleared');
}

function fit_boxes(length, width, height) {
    const large_v = 69 * 47 * 47;
    const medium_v = 48 * 45 * 42;
    const small_v = 47 * 33 * 30;

    let volume = length * width * height;
    let box_count = { small: 0, medium: 0, large: 0 };
    let total_volume = volume;

    while (volume >= large_v) {
        volume -= large_v;
        box_count.large++;
    }
    while (volume < large_v && volume >= medium_v) {
        volume -= medium_v;
        box_count.medium++;
    }
    while (volume < medium_v && volume >= small_v) {
        volume -= small_v;
        box_count.small++;
    }
    if (volume > 0) {
        box_count.small++;
    }

    let car_count = total_volume / 100000;
    car_count = Math.ceil(car_count * 2) / 2;

    console.log('Calculated boxes and car:', { ...box_count, car: car_count });

    return { ...box_count, car: car_count };
}

function calculateVolume() {
    const length = parseFloat(document.getElementById('length').value);
    const width = parseFloat(document.getElementById('width').value);
    const height = parseFloat(document.getElementById('height').value);

    if (!isNaN(length) && length > 0 && !isNaN(width) && width > 0 && !isNaN(height) && height > 0) {
        const { small, medium, large, car } = fit_boxes(length, width, height);
        document.getElementById('large').value = large;
        document.getElementById('medium').value = medium;
        document.getElementById('small').value = small;
        document.getElementById('car-estimate').value = car;
    } else {
        document.getElementById('large').value = '';
        document.getElementById('medium').value = '';
        document.getElementById('small').value = '';
        document.getElementById('car-estimate').value = '';
    }
    console.log('Volume calculated and fields updated');
}
