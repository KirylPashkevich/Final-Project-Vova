const userId = localStorage.getItem('whorehouse_user_id')
const container = document.getElementById('card-container')
const emptyMsg = document.getElementById('empty-msg')

// Проверка наличия userId
if (!userId) {
    console.warn('User ID не найден в localStorage')
    if (emptyMsg) {
        emptyMsg.style.display = 'block'
        emptyMsg.textContent = 'Пожалуйста, авторизуйтесь'
    }
}

async function loadCart() {
    if (!userId) {
        console.error('Невозможно загрузить корзину: отсутствует user_id')
        return
    }
    
    const API_URL = `/cart?user_id=${userId}`
    
    try {
        const response = await fetch(API_URL)
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const cartData = await response.json()
        
        if (Object.keys(cartData).length === 0) {
            if (emptyMsg) {
                emptyMsg.style.display = 'block'
                emptyMsg.textContent = 'Ваша корзина пуста'
            }
            if (container) {
                container.innerHTML = ''
            }
            return
        }
        
        if (emptyMsg) {
            emptyMsg.style.display = 'none'
        }
        
        await renderCart(cartData)
        
    } catch(error) {
        console.error("Ошибка при загрузке с сервера:", error)
        if (emptyMsg) {
            emptyMsg.style.display = 'block'
            emptyMsg.textContent = 'Ошибка загрузки корзины. Проверьте подключение к серверу.'
        }
    }
}

async function renderCart(cartData) {
    if (!container) {
        console.error('Контейнер для отображения корзины не найден')
        return
    }
    
    container.innerHTML = ""
    
    for (const itemId in cartData) {
        const quantity = cartData[itemId]
        
        try {
            const res = await fetch(`/items/${itemId}`)
            
            if (!res.ok) {
                console.error(`Ошибка загрузки товара ${itemId}: ${res.status}`)
                continue
            }
            
            const item = await res.json()
            
            const card = document.createElement('div')
            card.className = 'card'
            card.innerHTML = `
                <div class="card-content">
                    <h3 class="card-title">${escapeHtml(item.name)}</h3>
                    <p class="card-quantity">📦 Количество в заказе: <b>${quantity} шт.</b></p>
                    <p class="card-weight">⚖️ Общий вес: <b>${(item.weight * quantity).toFixed(2)} кг</b></p>
                    ${item.is_dangerous ? '<p class="danger-badge">⚠️ Опасный груз</p>' : ''}
                </div>
            `
            container.appendChild(card)
            
        } catch (error) {
            console.error(`Ошибка при обработке товара ${itemId}:`, error)
        }
    }
    
    // Если после загрузки нет товаров в корзине
    if (container.children.length === 0) {
        if (emptyMsg) {
            emptyMsg.style.display = 'block'
            emptyMsg.textContent = 'Корзина пуста или не удалось загрузить товары'
        }
    }
}

// Функция для экранирования HTML спецсимволов (безопасность)
function escapeHtml(text) {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
}

// Загружаем корзину при загрузке страницы
loadCart()

// Опционально: автоматическое обновление корзины каждые 30 секунд
// setInterval(loadCart, 30000)