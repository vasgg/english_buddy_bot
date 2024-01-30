
function randomInteger(min, max) {
// случайное число от min до (max+1)
let rand = min + Math.random() * (max + 1 - min);
return Math.floor(rand);
}

function addReaction(type) {

const randomNum = randomInteger(1000, 9000000)
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


document.addEventListener("DOMContentLoaded", () => {
const textareas = document.querySelectorAll('textarea');
textareas.forEach(textarea => {
    autoResizeTextarea.call(textarea);
    textarea.addEventListener('input', autoResizeTextarea);
});


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


function addNewSlide(slideId) {
    fetch('/add-slide', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ slide_id: slideId })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log(data.message);
        // Обновление интерфейса после добавления слайда
    })
    .catch(error => {
        console.error("Could not add new slide:", error);
    });



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

document.getElementById('editLessonForm').onsubmit = async function(e) {
    e.preventDefault(); // Предотвращаем стандартную отправку формы
    let formData = new FormData(this);
    let response = await fetch('/edit-lesson/{{ lesson.id }}', {
        method: 'POST',
        body: formData
    });
    let result = await response.json();
    if (response.ok) {
        alert(result.message); // Показываем сообщение
        // Опционально: добавьте логику для обновления страницы или перехода на другую страницу
    } else {
        alert("Ошибка при сохранении: " + result.detail); // Показываем ошибку
    }
};
