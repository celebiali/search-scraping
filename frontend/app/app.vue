<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Trash2, ExternalLink, RefreshCw, ShoppingCart, Tag, Bell } from 'lucide-vue-next'

const config = useRuntimeConfig()
const products = ref([])
const newQuery = ref('')
const newCategory = ref('elektronik')
const isSubmitting = ref(false)
const notificationStatus = ref('default')

const fetchProducts = async () => {
  try {
    const data = await $fetch(`${config.public.apiBase}/products`)
    products.value = data
  } catch (err) {
    console.error('Fetch error:', err)
  }
}

const subscribeToPush = async () => {
  if (!('serviceWorker' in navigator)) return
  
  try {
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: 'BJ_M-k3V_V1xI-MvX-B7Gj_jB_vX-S1j-B7Gj_jB_vX-S1j'
    })
    
    await $fetch(`${config.public.apiBase}/subscribe`, {
      method: 'POST',
      body: JSON.parse(JSON.stringify(subscription))
    })
    
    notificationStatus.value = 'granted'
    alert('Bildirimler başarıyla açıldı!')
  } catch (err) {
    console.error('Subscription error:', err)
    alert('Bildirim kaydı başarısız oldu.')
  }
}

const checkNotificationPermission = () => {
  if (typeof window !== 'undefined' && 'Notification' in window) {
    notificationStatus.value = Notification.permission
  }
}

const categories = [
  { id: 'elektronik', name: 'Elektronik' },
  { id: 'giyim', name: 'Giyim' },
  { id: 'kozmetik', name: 'Kozmetik' },
  { id: 'ev-yasam', name: 'Ev & Yaşam' }
]

const fetchProducts = async () => {
  try {
    const data = await $fetch(`${config.public.apiBase}/products`)
    products.value = data
  } catch (err) {
    console.error('Fetch error:', err)
  }
}

const addProduct = async () => {
  if (!newQuery.value) return
  isSubmitting.value = true
  try {
    await $fetch(`${config.public.apiBase}/products`, {
      method: 'POST',
      body: {
        query: newQuery.value,
        category: newCategory.value
      }
    })
    newQuery.value = ''
    await fetchProducts()
  } catch (err) {
    console.error('Add error:', err)
  } finally {
    isSubmitting.value = false
  }
}

const deleteProduct = async (id) => {
  try {
    await $fetch(`${config.public.apiBase}/products/${id}`, {
      method: 'DELETE'
    })
    await fetchProducts()
  } catch (err) {
    console.error('Delete error:', err)
  }
}

const toggleStatus = async (id) => {
  try {
    await $fetch(`${config.public.apiBase}/products/${id}/toggle`, {
      method: 'POST'
    })
    await fetchProducts()
  } catch (err) {
    console.error('Toggle error:', err)
  }
}

onMounted(() => {
  fetchProducts()
  checkNotificationPermission()
  // 30 saniyede bir güncelle
  setInterval(fetchProducts, 30000)
})
</script>

<template>
  <div class="container animate-fade-in">
    <header class="header">
      <div class="logo-area">
        <div class="logo-icon">
          <ShoppingCart :size="32" />
        </div>
        <div>
          <h1>Smart Tracker</h1>
          <p>Universal E-Ticaret Takip Sistemi</p>
        </div>
      </div>
      <div class="header-actions">
        <button v-if="notificationStatus !== 'granted'" class="btn btn-outline" @click="subscribeToPush">
          <Bell :size="18" />
          Bildirimleri Aç
        </button>
        <div class="status-badge">
          <div class="pulse-dot"></div>
          Live Monitoring
        </div>
      </div>
    </header>

    <div class="grid">
      <!-- Takip Ekle -->
      <section class="add-section glass-card">
        <h2 class="section-title">Yeni Takip Ekle</h2>
        <div class="form-group">
          <label>Ürün Adı / Model</label>
          <input 
            v-model="newQuery" 
            type="text" 
            placeholder="Örn: iPhone 15 128 GB" 
            @keyup.enter="addProduct"
          />
        </div>
        <div class="form-group">
          <label>Kategori</label>
          <select v-model="newCategory">
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">
              {{ cat.name }}
            </option>
          </select>
        </div>
        <button 
          class="btn btn-primary w-full" 
          :disabled="isSubmitting"
          @click="addProduct"
        >
          <Plus :size="20" />
          {{ isSubmitting ? 'Ekleniyor...' : 'Takibe Al' }}
        </button>
      </section>

      <!-- Ürün Listesi -->
      <section class="list-section">
        <div class="list-header">
          <h2 class="section-title">Takip Edilenler ({{ products.length }})</h2>
          <button class="refresh-btn" @click="fetchProducts">
            <RefreshCw :size="18" />
          </button>
        </div>

        <div v-if="products.length === 0" class="empty-state glass-card">
          Henüz takip edilen ürün yok. Hemen bir tane ekleyin!
        </div>

        <div class="product-grid">
          <div 
            v-for="product in products" 
            :key="product.id" 
            class="product-card glass-card"
            :class="{ 'inactive': !product.is_active }"
          >
            <div class="card-header">
              <span class="category-tag">{{ product.category }}</span>
              <div class="card-actions">
                <button class="icon-btn" @click="toggleStatus(product.id)">
                  <RefreshCw :size="16" />
                </button>
                <button class="icon-btn delete" @click="deleteProduct(product.id)">
                  <Trash2 :size="16" />
                </button>
              </div>
            </div>

            <h3 class="product-name">{{ product.last_name || product.query }}</h3>
            
            <div class="price-info">
              <div class="current-price">
                <label>Mevcut Fiyat</label>
                <span v-if="product.last_price">{{ product.last_price.toLocaleString('tr-TR') }} TL</span>
                <span v-else class="searching">Taranıyor...</span>
              </div>
              <div class="best-price">
                <label>En Düşük</label>
                <span>{{ product.best_price_ever ? product.best_price_ever.toLocaleString('tr-TR') + ' TL' : '-' }}</span>
              </div>
            </div>

            <div class="card-footer">
              <span class="source-tag" v-if="product.last_source">
                {{ product.last_source }}
              </span>
              <a 
                v-if="product.last_link" 
                :href="product.last_link" 
                target="_blank" 
                class="view-link"
              >
                Ürüne Git
                <ExternalLink :size="14" />
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3rem;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-icon {
  background: var(--accent);
  width: 56px;
  height: 56px;
  border-radius: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 16px rgba(56, 189, 248, 0.3);
}

h1 {
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.header p {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.status-badge {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success);
  padding: 0.5rem 1rem;
  border-radius: 2rem;
  font-size: 0.75rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: var(--success);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}

.grid {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 2rem;
}

@media (max-width: 1024px) {
  .grid { grid-template-columns: 1fr; }
}

.section-title {
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
  font-weight: 600;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.refresh-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  transition: color 0.2s;
}

.refresh-btn:hover {
  color: var(--accent);
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.product-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.product-card.inactive {
  opacity: 0.6;
  grayscale: 1;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-tag {
  background: rgba(148, 163, 184, 0.1);
  padding: 0.25rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  text-transform: capitalize;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
}

.icon-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
}

.icon-btn:hover { color: var(--accent); }
.icon-btn.delete:hover { color: var(--danger); }

.product-name {
  font-size: 1rem;
  font-weight: 500;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  height: 3rem;
}

.price-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 1rem 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.price-info label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.current-price span {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--accent);
}

.best-price span {
  font-weight: 600;
}

.searching {
  font-size: 0.875rem !important;
  font-weight: 400 !important;
  font-style: italic;
  opacity: 0.7;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.source-tag {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.view-link {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--accent);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 600;
}

.view-link:hover {
  text-decoration: underline;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
}

.w-full { width: 100%; }
</style>
