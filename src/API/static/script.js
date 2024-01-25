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

function addReaction(type) {
    // Получаем контейнер для правильных или неправильных реакций
    const container = document.getElementById(`${type}-reactions`);

    // Создаем новый элемент input
    const inputGroup = document.createElement('div');
    inputGroup.className = 'input-group mb-2';

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control';
    input.name = `${type}_new`; // Важно установить уникальное имя для нового поля

    const inputGroupAppend = document.createElement('div');
    inputGroupAppend.className = 'input-group-append';

    const deleteButton = document.createElement('button');
    deleteButton.className = 'btn btn-danger';
    deleteButton.type = 'button';
    deleteButton.textContent = '-';
    deleteButton.onclick = function() {
        // Определить логику для удаления элемента из DOM
    };

    inputGroupAppend.appendChild(deleteButton);
    inputGroup.appendChild(input);
    inputGroup.appendChild(inputGroupAppend);
    container.appendChild(inputGroup);
}

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

document.getElementById('editTextsForm').onsubmit = async function(e) {
    e.preventDefault(); // Предотвращаем стандартную отправку формы
    let formData = new FormData(this);
    let response = await fetch('/texts', {
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

// Функция для автоматической настройки высоты textarea
function autoResizeTextarea() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
}

// Применение функции ко всем элементам textarea при загрузке страницы
window.addEventListener('load', function() {
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        autoResizeTextarea.call(textarea);
        textarea.addEventListener('input', autoResizeTextarea);
    });
});
