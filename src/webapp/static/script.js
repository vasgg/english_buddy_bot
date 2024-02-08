// slides.html "+" button

let currentSlideId = null; // Глобальная переменная для хранения ID текущего слайда

// slide.html
async function saveSlide(slideId) {
    const form = document.getElementById('editSlideForm');
    const formData = new FormData(form);

    const jsonData = {};

    formData.forEach((value, key) => {
        if (!(value instanceof File)) {
            if (value.length > 0) {
                jsonData[key] = value;
            }
        } else {
            if (value.size > 0) {
            }
        }
    });

    if (formData.has('new_picture') && formData.get('new_picture').size > 0) {
        const fileData = new FormData();
        fileData.append('new_picture', formData.get('new_picture'));

        await sendFile(slideId, fileData);
    }

    await sendJsonData(slideId, jsonData);
}

async function sendJsonData(slideId, jsonData) {
    try {
        const response = await fetch(`/slides/${slideId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jsonData)
        });

        if (!response.ok) {
            throw new Error('Ошибка при отправке JSON данных');
        }

        alert('JSON данные успешно отправлены');
    } catch (error) {
        alert(error.message);
    }
}

async function sendFile(slideId, fileData) {
    try {
        const response = await fetch(`/slides/${slideId}/upload_picture`, {
            method: 'POST',
            body: fileData
        });

        if (!response.ok) {
            throw new Error('Ошибка при отправке файла');
        }

        alert('Файл успешно отправлен');
    } catch (error) {
        alert(error.message);
    }
}


// reactions.html
function randomInteger(min, max) {
    let rand = min + Math.random() * (max + 1 - min);
    return Math.floor(rand);
}


function addReaction(type) {
    const randomNum = randomInteger(1000, 9000)
    console.log('randomNum', randomNum)
    const container = document.getElementById(`${type}-reactions`);

    const inputGroup = document.createElement('div');
    inputGroup.className = 'reactions-input-wrapper mb-2';

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control';
    input.name = `${type}_${randomNum}_new`;

    const inputGroupAppend = document.createElement('div');
    inputGroupAppend.className = 'input-group-append';

    const deleteButton = document.createElement('button');
    deleteButton.className = 'btn btn-danger btn-square';
    deleteButton.type = 'button';
    deleteButton.textContent = '-';

    deleteButton.onclick = function(e) {
        const target = e.target;
        const parent = target.parentElement.parentElement

        parent.remove()
    };


    inputGroupAppend.appendChild(deleteButton);
    inputGroup.appendChild(input);
    inputGroup.appendChild(inputGroupAppend);
    container.appendChild(inputGroup);
}


// reactions.html "-" button
function confirmDeletion(reactionId) {
        if (confirm('Вы уверены, что хотите удалить эту реакцию?')) {
        fetch(`/reactions/${reactionId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            window.location.reload();
        })
        .catch(error => {
            alert('Ошибка при удалении: ' + error);
        });
    }
}
// slides.html "✏️" button
function editSlide(slideId) {
    window.location.href = `/slides/${slideId}`;
}

// base.html "Редактирование текстов" button
function editTextsButton() {
    window.location.href = `/texts/`;
}

// base.html "Редактирование реакций" button
function editReactionsButton() {
    window.location.href = `/reactions/`;
}

// base.html "Список уроков" button
function lessonListButton() {
    window.location.href = `/lessons/`;
}

// lesson.html "Слайды" button
function showSlides(lessonId) {
    window.location.href = `/lesson_${lessonId}/slides`;
}

// lesson.html "Добавить урок" button
function addLessonButton() {
    window.location.href = `/add-lesson/`;
}

const SwitchSlideButtons = document.querySelectorAll('.SwitchSlideButton')
if (SwitchSlideButtons.length) {
    SwitchSlideButtons.forEach(button => {
        button.addEventListener(('click'), () => {
            const dataParam = button.getAttribute("data-link-slide");
            window.location.href = `/slides/${dataParam}`;
        })
    })
}

// slides.html "+" button
function showModalWithSlideId(slideId) {
    currentSlideId = slideId; // Запоминаем ID слайда
    document.getElementById('slideTypeDialog').showModal();
}

function selectSlideType(slideType) {
    document.getElementById('slideTypeDialog').close();

    console.log(`Выбран тип слайда: ${slideType} для слайда с ID ${currentSlideId}`);

    fetch('/add-slide', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            slide_type: slideType,
            slide_id: currentSlideId,
        }),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
        window.location.reload();
    })
    .catch(error => {
        console.error('Ошибка при добавлении нового слайда:', error);
    });
}

// slides.html "-" button
function confirmSlideDeletion(slideId) {
    if (confirm(`Вы уверены, что хотите удалить слайд ID ${slideId}?`)) {
        fetch(`/slides/${slideId}`, {
            method: 'DELETE',
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Проблема при попытке удаления слайда.');
        })
        .then(data => {
            alert(`Слайд ${slideId} был успешно удален.`);
            window.location.reload();
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert("Ошибка при удалении слайда.");
        });
    } else {
        console.log("Удаление отменено.");
    }
}

// slides.html "∆" and "∇" button
function moveSlideUp(button) {
    const slideRow = button.closest('tr');
    if (slideRow.previousElementSibling) {
        slideRow.parentNode.insertBefore(slideRow, slideRow.previousElementSibling);
    }
}

function moveSlideDown(button) {
    const slideRow = button.closest('tr');
    if (slideRow.nextElementSibling) {
        slideRow.parentNode.insertBefore(slideRow.nextElementSibling, slideRow);
    }
}
// slides.html save slides order
function saveSlideOrder() {
    const slides = document.querySelectorAll('#slidesTable tr');
    const orderData = Array.from(slides).map(slide => ({
        slide_id: parseInt(slide.getAttribute('data-slide-id'), 10),
        lesson_id: parseInt(slide.getAttribute('data-lesson-id'), 10),
        next_slide_id: slide.nextElementSibling ? parseInt(slide.nextElementSibling.getAttribute('data-slide-id'), 10) : null
    }));

    fetch('/save-slides-order', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({slides: orderData})
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        window.location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error saving slide order.');
    });
};

// Функция для автоматической настройки высоты textarea
function autoResizeTextarea() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
}



document.addEventListener("DOMContentLoaded", () => {
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        autoResizeTextarea.call(textarea);
        textarea.addEventListener('input', autoResizeTextarea);
    });

    document.getElementById('editTextsForm').onsubmit = async function(e) {
        e.preventDefault(); // Предотвращаем стандартную отправку формы
        console.log('e =>', e)

        let formData = new FormData(this);

        try {
            let response = await fetch('/texts', {
                method: 'POST',
                body: formData
            });
            let result = await response.json();

            if (response.ok) {
                alert(result.message); // Показываем сообщение
            } else {
                alert("Ошибка при сохранении: " + result.detail); // Показываем ошибку
            }

        } catch (e) {
            alert("Сервер не отвечает"); // Показываем ошибку
        }
    };
});

// lesson.html
const SwitchLessonButtons = document.querySelectorAll('.SwitchLessonButton')
if (SwitchLessonButtons.length) {
    SwitchLessonButtons.forEach(button => {
        button.addEventListener(('click'), () => {
            const dataParam = button.getAttribute("data-link-slide");
            window.location.href = `/lesson/${dataParam}`;
        })
    })
}

function saveLesson() {
    const form = document.getElementById('editLessonForm');
    const formData = new FormData(form);
    const object = {};
    formData.forEach((value, key) => {
    // Если значение равно "None", не включаем его в объект данных
    // Или можно присвоить null или другое специальное значение
    if (value !== "None") {
        object[key] = value;
    } else {
        // Здесь можно задать значение по умолчанию или не добавлять ключ вовсе
        // Например: object[key] = null; или просто пропустить
    }
    });

    fetch(form.action, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(object),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Сетевая ошибка при попытке обновления');
        }
        return response.json();
    })
    .then(data => {
        alert(data.message || 'Данные успешно обновлены');
        window.location.reload();
    })
    .catch(error => {
        alert('Ошибка: ' + error.message);
    });
}
