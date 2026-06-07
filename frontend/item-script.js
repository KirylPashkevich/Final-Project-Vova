document.addEventListener("DOMContentLoaded", async ()=> {
    const urlParams = new URLSearchParams(window.location.search)
    const itemId = urlParams.get('id')
    if(!itemId){
        alert("Товар не найдет или не выбран!!!!")
        window.location.href = "index.html"
        return
    }
    const API_URL = `/items/${itemId}`;
    try{
        const response = await fetch(API_URL);
        if (!response.ok){
            throw new Error("Товар не найден на сервере")
        }
        const item = await response.json();
        document.getElementById('item-name').textContent = item.name
        document.getElementById('item-sector').textContent = item.storage_sector
        document.getElementById('item-quantity').textContent = item.quantity
        document.getElementById('item-weight').textContent = item.weight

        const imageElement = document.getElementById('item-image')
        if(item.image){
            imageElement.src = item.image
        }
        else{
            imageElement.src = `/static/img/default.jpg`
        }
        if(item.is_dangerous){
            document.getElementById('danger-badge').style.display = 'block';
        }

        const deleteBtn = document.getElementById('delete-btn');
        deleteBtn.addEventListener('click', async () => {
            if (!confirm('Вы уверены, что хотите списать этот товар со склада?')) return;
            try {
                const delResponse = await fetch(`/items/${itemId}?confirm=true`, { method: 'DELETE' });
                if (delResponse.ok) {
                    alert('Товар списан со склада');
                    window.location.href = 'index.html';
                } else {
                    const errData = await delResponse.json();
                    alert(errData.detail || 'Ошибка при удалении');
                }
            } catch (err) {
                console.error('Ошибка удаления:', err);
                alert('Ошибка сети при удалении');
            }
        });

    } catch(error){
        console.error("ошибка:", error)
        document.getElementById('item-name').textContent = "Ошибка загрузки элемента"
    }
})