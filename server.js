// =========================================================
// GreenLeaf Full-Stack Node.js & Express Backend Server
// =========================================================
const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 5000;

// Enable CORS and JSON body parser
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Database / File Storage
const DATA_FILE = path.join(__dirname, 'store.json');

// Default Seed Plants
const defaultPlants = [
  { id: 1, name: "Snake Plant", category: "indoor", price: 399, oldPrice: 499, discount: 20, rating: 4.8, reviews: 128, image: "images/Snake Plant.jpg", description: "A hardy indoor plant that is easy to maintain.", type: "Indoor Plant", light: "Low to Bright", water: "Low", suitable: "Home & Office" },
  { id: 2, name: "Monstera Deliciosa", category: "indoor", price: 699, oldPrice: 899, discount: 22, rating: 4.9, reviews: 214, image: "images/Monstera Deliciosa.jpg", description: "A tropical plant with beautiful split leaves.", type: "Tropical", light: "Indirect", water: "Medium", suitable: "Living Room" },
  { id: 3, name: "Aloe Vera", category: "succulent", price: 299, oldPrice: 399, discount: 25, rating: 4.8, reviews: 191, image: "images/Aloe Vera.jpg", description: "A useful succulent requiring minimal care.", type: "Succulent", light: "Bright", water: "Low", suitable: "Home" },
  { id: 4, name: "Areca Palm", category: "indoor", price: 899, oldPrice: 1199, discount: 25, rating: 4.6, reviews: 94, image: "images/Areca Palm.jpg", description: "A graceful palm that adds a tropical green touch.", type: "Palm", light: "Bright", water: "Medium", suitable: "Living Room" },
  { id: 5, name: "Money Plant (Golden Pothos)", category: "indoor", price: 349, oldPrice: 449, discount: 22, rating: 4.8, reviews: 312, image: "images/Money Plant (Golden Pothos).jpg", description: "A popular easy-care plant with trailing vines.", type: "Climber", light: "Indirect", water: "Medium", suitable: "Home & Office" },
  { id: 6, name: "Red Rose Plant", category: "flowering", price: 549, oldPrice: 699, discount: 21, rating: 4.7, reviews: 183, image: "images/Red Rose Plant.jpg", description: "Classic flowering plant with fragrant blooms.", type: "Flowering", light: "Bright", water: "Medium", suitable: "Garden" },
  { id: 7, name: "Jade Plant", category: "succulent", price: 449, oldPrice: 599, discount: 25, rating: 4.8, reviews: 145, image: "images/Jade Plant.jpg", description: "Compact succulent with thick leaves.", type: "Succulent", light: "Bright", water: "Low", suitable: "Desk & Home" },
  { id: 8, name: "Rubber Plant (Ficus Elastica)", category: "indoor", price: 799, oldPrice: 999, discount: 20, rating: 4.7, reviews: 121, image: "images/Rubber Plant (Ficus Elastica).jpg", description: "A bold indoor plant with glossy leaves.", type: "Indoor", light: "Indirect", water: "Medium", suitable: "Living Room" }
];

let store = {
  plants: [...defaultPlants],
  orders: [],
  messages: []
};

// Load saved data from store.json if exists
if (fs.existsSync(DATA_FILE)) {
  try {
    const saved = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
    if (saved && typeof saved === 'object') {
      store.plants = Array.isArray(saved.plants) && saved.plants.length > 0 ? saved.plants : [...defaultPlants];
      store.orders = Array.isArray(saved.orders) ? saved.orders : [];
      store.messages = Array.isArray(saved.messages) ? saved.messages : [];
    }
  } catch (e) {
    console.error("Error reading store.json", e);
  }
} else {
  saveStore();
}

function saveStore() {
  try {
    fs.writeFileSync(DATA_FILE, JSON.stringify(store, null, 2), 'utf8');
  } catch (e) {
    console.error("Error saving store.json", e);
  }
}

// -------------------------------------------------------------
// 1. ADMIN AUTHENTICATION API
// -------------------------------------------------------------
app.post('/api/admin/login', (req, res) => {
  const { username, password } = req.body || {};
  if (username === 'admin' && password === 'admin123') {
    const token = crypto.createHash('sha256').update(`admin:${Date.now()}`).digest('hex');
    return res.json({ success: true, token, username: 'admin', message: 'Admin authenticated' });
  }
  return res.status(401).json({ success: false, error: 'Invalid username or password' });
});

// -------------------------------------------------------------
// 2. PLANT INVENTORY API
// -------------------------------------------------------------
// Get all plants
app.get('/api/plants', (req, res) => {
  res.json(store.plants);
});

// Sync all plants from frontend
app.put('/api/plants', (req, res) => {
  if (Array.isArray(req.body)) {
    store.plants = req.body;
    saveStore();
    return res.json({ success: true, count: store.plants.length });
  }
  res.status(400).json({ error: 'Expected array of plants' });
});

// Add new plant
app.post('/api/plants', (req, res) => {
  const newPlant = { id: Date.now(), ...req.body };
  store.plants.unshift(newPlant);
  saveStore();
  res.json({ success: true, plant: newPlant });
});

// Edit plant
app.put('/api/plants/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const index = store.plants.findIndex(p => p.id === id);
  if (index !== -1) {
    store.plants[index] = { ...store.plants[index], ...req.body, id };
    saveStore();
    return res.json({ success: true, plant: store.plants[index] });
  }
  res.status(404).json({ error: 'Plant not found' });
});

// Delete plant
app.delete('/api/plants/:id', (req, res) => {
  const id = parseInt(req.params.id);
  store.plants = store.plants.filter(p => p.id !== id);
  saveStore();
  res.json({ success: true, message: 'Plant deleted' });
});

// -------------------------------------------------------------
// 3. ORDERS API
// -------------------------------------------------------------
// Get all orders
app.get('/api/orders', (req, res) => {
  res.json(store.orders);
});

// Sync all orders from frontend
app.put('/api/orders', (req, res) => {
  if (Array.isArray(req.body)) {
    store.orders = req.body;
    saveStore();
    return res.json({ success: true, count: store.orders.length });
  }
  res.status(400).json({ error: 'Expected array of orders' });
});

// Place order
app.post('/api/orders', (req, res) => {
  const orderId = req.body.orderId || ('GL-' + Math.floor(100000 + Math.random() * 900000));
  const newOrder = {
    orderId,
    date: req.body.date || new Date().toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' }),
    status: 'Processing',
    ...req.body
  };
  store.orders.unshift(newOrder);
  saveStore();
  res.json({ success: true, order: newOrder });
});

// Update order fulfillment status
app.put('/api/orders/:id/status', (req, res) => {
  const orderId = req.params.id;
  const { status } = req.body;
  const ord = store.orders.find(o => String(o.orderId) === String(orderId) || String(o.id) === String(orderId));
  if (ord) {
    ord.status = status || 'Processing';
    saveStore();
    return res.json({ success: true, order: ord });
  }
  res.status(404).json({ error: 'Order not found' });
});

// Delete order
app.delete('/api/orders/:id', (req, res) => {
  const orderId = req.params.id;
  store.orders = store.orders.filter(o => String(o.orderId) !== String(orderId) && String(o.id) !== String(orderId));
  saveStore();
  res.json({ success: true, message: 'Order deleted' });
});

// Clear all orders
app.delete('/api/orders', (req, res) => {
  store.orders = [];
  saveStore();
  res.json({ success: true, message: 'All orders cleared' });
});

// -------------------------------------------------------------
// 4. CONTACT INQUIRIES API
// -------------------------------------------------------------
app.get('/api/messages', (req, res) => res.json(store.messages));

app.post('/api/messages', (req, res) => {
  const newMsg = {
    id: Date.now(),
    date: new Date().toLocaleDateString('en-IN'),
    ...req.body
  };
  store.messages.unshift(newMsg);
  saveStore();
  res.json({ success: true, message: newMsg });
});

app.delete('/api/messages/:id', (req, res) => {
  const id = parseInt(req.params.id);
  store.messages = store.messages.filter(m => m.id !== id);
  saveStore();
  res.json({ success: true, message: 'Message deleted' });
});

// -------------------------------------------------------------
// 5. DASHBOARD STATS API
// -------------------------------------------------------------
app.get('/api/dashboard/stats', (req, res) => {
  const totalRevenue = store.orders.reduce((sum, o) => sum + (o.status !== 'Cancelled' ? (o.total || 0) : 0), 0);
  res.json({
    total_plants: store.plants.length,
    total_orders: store.orders.length,
    total_revenue: totalRevenue,
    total_messages: store.messages.length
  });
});

// -------------------------------------------------------------
// 6. SERVE STATIC FRONTEND
// -------------------------------------------------------------
app.use(express.static(path.join(__dirname)));

app.get('*', (req, res) => {
  const indexPath = path.join(__dirname, 'index.html');
  if (fs.existsSync(indexPath)) {
    return res.sendFile(indexPath);
  }
  res.status(404).send('index.html not found');
});

// Start Server
app.listen(PORT, () => {
  console.log(`🌱 GreenLeaf Backend Server running at: http://localhost:${PORT}`);
  console.log(`🔐 Admin Panel: http://localhost:${PORT} (Username: admin | Password: admin123)`);
});