// reactions.html
function randomInteger(min, max) {
    let rand = min + Math.random() * (max + 1 - min);
    return Math.floor(rand);
}


function addReaction(type) {
    const randomNum = randomInteger(1000, 9000)
    console.log('randomNum', randomNum)
    // Получаем контейнер для правильных или неправильных реакций
    const container = document.getElementById(`${type}-reactions`);

    // Создаем новый элемент div
    const inputGroup = document.createElement('div');
    inputGroup.className = 'reactions-input-wrapper mb-2';

    // Создаем новый элемент input
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control';
    input.name = `${type}_${randomNum}_new`; // Важно установить уникальное имя для нового поля

    // Создаем новый div для кнопки
    const inputGroupAppend = document.createElement('div');
    inputGroupAppend.className = 'input-group-append';

    // Создаем новый элемент кнопку для удаления
    const deleteButton = document.createElement('button');
    deleteButton.className = 'btn btn-danger btn-square';
    deleteButton.type = 'button';
    deleteButton.textContent = '-';

    // Логика для удаления элемента из DOM
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

    // slides.html save slides order
document.getElementById('saveOrderBtn').addEventListener('click', function() {
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
});


// reactions.html "-" button
function confirmDeletion(reactionId) {
        if (confirm('Вы уверены, что хотите удалить эту реакцию?')) {
        fetch(`/reactions/${reactionId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            window.location.reload(); // Перезагружаем страницу для отображения изменений
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

// lesson.html "Добавить урок" button
function addLessonButton() {
    window.location.href = `/add-lesson/`;
}


// slides.html "+" button
let currentSlideId = null; // Глобальная переменная для хранения ID текущего слайда

function showModalWithSlideId(slideId) {
    currentSlideId = slideId; // Запоминаем ID слайда
    document.getElementById('slideTypeDialog').showModal();
}

function selectSlideType(slideType) {
    // Закрыть диалоговое окно после выбора
    document.getElementById('slideTypeDialog').close();

    console.log(`Выбран тип слайда: ${slideType} для слайда с ID ${currentSlideId}`);

    // Отправляем данные на сервер
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
        alert(data.message);

        // Действия после успешного добавления, например, обновление интерфейса
    })
    .catch(error => {
        console.error('Ошибка при добавлении нового слайда:', error);
    });
}
// slides.html "-" button
function confirmSlideDeletion(slideId) {
    // Показываем диалоговое окно для подтверждения
    if (confirm("Вы уверены, что хотите удалить этот слайд?")) {
        // Пользователь подтвердил удаление, отправляем запрос на сервер
        fetch(`/slides/${slideId}`, {
            method: 'DELETE',
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            // Обрабатываем возможные ошибки HTTP
            throw new Error('Проблема при попытке удаления слайда.');
        })
        .then(data => {
            // Отображаем сообщение об успешном удалении
            alert("Слайд был успешно удален.");
            // Обновляем страницу, чтобы отразить изменения
            window.location.reload();
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert("Ошибка при удалении слайда.");
        });
    } else {
        // Пользователь отменил удаление
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

    document.getElementById('editReactionsForm').onsubmit = async function(e) {
        e.preventDefault(); // Предотвращаем стандартную отправку формы
        let formData = new FormData(this);
        let response = await fetch('/reactions', {
            method: 'POST',
            body: formData
        });
        let result = await response.json();
        if (response.ok) {
            alert(result.message); // Показываем сообщение
            window.location.reload(); // Перезагружаем страницу
        } else {
            alert("Ошибка при сохранении: " + result.detail); // Показываем ошибку
        }
    };

});
