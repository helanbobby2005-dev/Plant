// GreenLeaf Backend Integration Bridge
// Seamlessly connects the existing frontend UI with backend APIs without modifying index.html

(function() {
    console.log("🌿 GreenLeaf Backend Bridge initialized");

    // 1. Fetch live plants from backend and update UI
    async function loadLivePlants() {
        try {
            const res = await fetch("/api/plants");
            if (res.ok) {
                const livePlants = await res.json();
                if (Array.isArray(livePlants) && livePlants.length > 0) {
                    // Update global plants array in-place so all existing listeners/references stay intact
                    plants.length = 0;
                    livePlants.forEach(p => plants.push(p));
                    
                    const totalElem = document.getElementById("plantTotal");
                    if (totalElem) totalElem.innerText = plants.length + "+ Plants";

                    // Re-render UI views
                    if (typeof renderHomePlants === "function") renderHomePlants();
                    if (typeof renderPlants === "function") renderPlants();
                    if (typeof renderWishlistPage === "function") renderWishlistPage();
                    if (typeof renderCartPage === "function") renderCartPage();
                    if (typeof renderCheckoutSummary === "function") renderCheckoutSummary();
                }
            }
        } catch (err) {
            console.warn("Backend API unavailable, using offline fallback plants.", err);
        }
    }

    // 2. Intercept checkout order placement to persist in backend database
    window.placeOrder = async function(event) {
        event.preventDefault();

        if (cart.length === 0) {
            if (typeof showToast === "function") showToast("Your cart is empty.");
            return;
        }

        const name = document.getElementById("customerName")?.value || "";
        const phone = document.getElementById("customerPhone")?.value || "";
        const email = document.getElementById("customerEmail")?.value || "";
        const pincode = document.getElementById("customerPincode")?.value || "";
        const address = document.getElementById("customerAddress")?.value || "";
        const city = document.getElementById("customerCity")?.value || "";
        const state = document.getElementById("customerState")?.value || "";
        const payment = document.querySelector('input[name="payment"]:checked')?.value || "UPI";

        const totals = typeof getCartTotals === "function" ? getCartTotals() : { total: 0 };

        const orderData = {
            customer_name: name,
            customer_phone: phone,
            customer_email: email,
            customer_pincode: pincode,
            customer_address: address,
            customer_city: city,
            customer_state: state,
            payment_method: payment,
            items: cart.map(i => ({
                id: i.id,
                name: i.name,
                price: i.price,
                quantity: i.quantity || 1,
                image: i.image,
                category: i.category
            })),
            total_amount: totals.total
        };

        try {
            const res = await fetch("/api/orders", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(orderData)
            });

            if (res.ok) {
                const resData = await res.json();
                if (typeof showToast === "function") {
                    showToast(`Thank you ${name}! Order #${resData.order_id || 'GL-' + Date.now()} placed via ${payment}.`);
                }
            } else {
                if (typeof showToast === "function") {
                    showToast(`Thank you ${name}! Order placed via ${payment}.`);
                }
            }
        } catch (err) {
            console.error("Order save error:", err);
            if (typeof showToast === "function") {
                showToast(`Thank you ${name}! Order placed via ${payment}.`);
            }
        }

        // Clear cart and UI
        cart = [];
        if (typeof saveData === "function") saveData();
        if (typeof updateCounts === "function") updateCounts();

        const form = document.getElementById("checkoutForm");
        if (form) form.reset();

        setTimeout(() => {
            if (typeof showPage === "function") showPage("home");
        }, 1800);
    };

    // 3. Intercept contact form submission to persist inquiries in backend database
    window.submitContact = async function(event) {
        event.preventDefault();
        const form = event.target;
        const nameInput = form.querySelector('input[type="text"]:first-of-type') || document.getElementById("contactName");
        const emailInput = form.querySelector('input[type="email"]');
        const subjectInput = form.querySelectorAll('input[type="text"]')[1];
        const messageInput = form.querySelector("textarea");

        const name = nameInput ? nameInput.value : "";
        const email = emailInput ? emailInput.value : "";
        const subject = subjectInput ? subjectInput.value : "";
        const message = messageInput ? messageInput.value : "";

        try {
            await fetch("/api/contacts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, subject, message })
            });
        } catch (e) {
            console.warn("Could not post contact form to backend:", e);
        }

        if (typeof showToast === "function") {
            showToast("Thank you, " + name + "! Your message has been received.");
        }
        form.reset();
    };

    // 4. Inject Admin Link into the navigation bar
    function addAdminNavLink() {
        const nav = document.querySelector(".nav-links");
        if (nav && !document.getElementById("nav-admin-link")) {
            const adminBtn = document.createElement("a");
            adminBtn.id = "nav-admin-link";
            adminBtn.href = "/admin.html";
            adminBtn.target = "_blank";
            adminBtn.style.cssText = "text-decoration:none; color:#255431; background:#e2f2e5; font-weight:600; font-size:12px; padding:6px 12px; border-radius:6px; display:inline-flex; align-items:center; gap:6px; border:1px solid #c0e3c6; margin-left:6px; transition:0.2s;";
            adminBtn.innerHTML = '<i class="fa-solid fa-lock"></i> Admin';
            adminBtn.onmouseover = () => adminBtn.style.background = "#d0ebd4";
            adminBtn.onmouseout = () => adminBtn.style.background = "#e2f2e5";
            nav.appendChild(adminBtn);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => {
            loadLivePlants();
            addAdminNavLink();
        });
    } else {
        loadLivePlants();
        addAdminNavLink();
    }
})();
