// ==========================
// START BUTTON (INDEX PAGE)
// ==========================
document.addEventListener("DOMContentLoaded", function () {

    const startBtn = document.querySelector(".start-btn");

    if (startBtn) {
        startBtn.addEventListener("click", function () {
            window.location.href = "/login";
        });
    }

});


// ==========================
// BODY PAGE FUNCTIONS
// ==========================
function kgToLbs() {
    let kg = document.getElementById("kg")?.value;
    if (kg) {
        document.getElementById("lbs").value = (kg * 2.20462).toFixed(2);
    }
}

function lbsToKg() {
    let lbs = document.getElementById("lbs")?.value;
    if (lbs) {
        document.getElementById("kg").value = (lbs / 2.20462).toFixed(2);
    }
}

function cmToFeet() {
    let cm = parseFloat(document.getElementById("cm")?.value);

    if (!isNaN(cm) && cm > 0) {
        let totalInches = cm / 2.54;
        let feet = Math.floor(totalInches / 12);
        let inches = Math.round(totalInches % 12);

        document.getElementById("feet").value = `${feet} ft ${inches} in`;
    }
}

function feetToCm() {
    let input = document.getElementById("feet")?.value.trim();
    let numbers = input.match(/\d+/g);

    if (numbers && numbers.length >= 2) {
        let feet = parseFloat(numbers[0]);
        let inches = parseFloat(numbers[1]);

        let cm = (feet * 30.48) + (inches * 2.54);

        document.getElementById("cm").value = cm.toFixed(2);
    } else {
        alert("Use format: 5 ft 7 in");
    }
}


// ==========================
// PERSONAL PAGE LOGIC (FIXED)
// ==========================
document.addEventListener("DOMContentLoaded", function () {

    // ===== ALLERGY =====
    const otherAllergy = document.getElementById("otherAllergy");
    const allergyBox = document.getElementById("otherAllergyBox");

    if (otherAllergy && allergyBox) {
        allergyBox.style.display = otherAllergy.checked ? "block" : "none";

        otherAllergy.addEventListener("change", function () {
            allergyBox.style.display = this.checked ? "block" : "none";

            if (!this.checked) allergyBox.value = ""; // 🔥 clear value
        });
    }

    // ===== CONDITION =====
    const otherCondition = document.getElementById("otherCondition");
    const conditionBox = document.getElementById("otherConditionBox");

    if (otherCondition && conditionBox) {
        conditionBox.style.display = otherCondition.checked ? "block" : "none";

        otherCondition.addEventListener("change", function () {
            conditionBox.style.display = this.checked ? "block" : "none";

            if (!this.checked) conditionBox.value = ""; // 🔥 clear value
        });
    }

    // ===== MEDICINE =====
    const medYes = document.getElementById("medYes");
    const medNo = document.getElementById("medNo");
    const medicineBox = document.getElementById("medicineBox");

    if (medYes && medNo && medicineBox) {

        // 🔥 Initial state
        if (medYes.checked) {
            medicineBox.style.display = "block";
            medicineBox.setAttribute("required", true);
        } else {
            medicineBox.style.display = "none";
            medicineBox.removeAttribute("required");
        }

        // YES selected
        medYes.addEventListener("change", function () {
            medicineBox.style.display = "block";
            medicineBox.setAttribute("required", true);
        });

        // NO selected
        medNo.addEventListener("change", function () {
            medicineBox.style.display = "none";
            medicineBox.removeAttribute("required");
            medicineBox.value = ""; // 🔥 clear value
        });
    }

});


// ==========================
// PERSONAL FORM VALIDATION
// ==========================
const personalForm = document.getElementById("personalForm");

if (personalForm) {
    personalForm.addEventListener("submit", function (e) {

        const allergies = document.querySelectorAll('input[name="allergies"]:checked');
        const conditions = document.querySelectorAll('input[name="conditions"]:checked');

        if (allergies.length === 0) {
            alert("Please select at least one allergy");
            e.preventDefault();
            return;
        }

        if (conditions.length === 0) {
            alert("Please select at least one health condition");
            e.preventDefault();
            return;
        }
    });
}


// ==========================
// BODY FORM VALIDATION + CLEAR
// ==========================
const bodyForm = document.getElementById("bodyForm");

if (bodyForm) {
    bodyForm.addEventListener("submit", function(e) {

        const inputs = bodyForm.querySelectorAll("input[required]");

        for (let input of inputs) {
            if (!input.value) {
                alert("Please fill all body measurements correctly");
                input.focus();
                e.preventDefault();
                return;
            }
        }

        // clear converter fields
        const kg = document.getElementById("kg");
        const lbs = document.getElementById("lbs");
        const cm = document.getElementById("cm");
        const feet = document.getElementById("feet");

        if (kg) kg.value = "";
        if (lbs) lbs.value = "";
        if (cm) cm.value = "";
        if (feet) feet.value = "";
    });
}

// ==========================
// DIET PAGE LOGIC
// ==========================
document.addEventListener("DOMContentLoaded", function () {

    // CARD SELECTION EFFECT
    document.querySelectorAll(".card-option").forEach(label => {
        label.addEventListener("click", function () {

            const name = this.querySelector("input").name;

            // remove selected from same group
            document.querySelectorAll(`input[name="${name}"]`).forEach(input => {
                input.parentElement.classList.remove("selected");
            });

            this.classList.add("selected");
        });
    });

    // DAY EXPAND / COLLAPSE
    document.querySelectorAll(".day-card").forEach(card => {
        card.addEventListener("click", function () {
            const content = this.querySelector(".day-content");
            content.classList.toggle("show");
        });
    });

    // LOADER
    const form = document.getElementById("dietForm");
    const loader = document.getElementById("loader");

    if(form){
        form.addEventListener("submit", function () {
            loader.style.display = "block";
        });
    }

});

// NONE LOGIC (Allergies + Conditions)
document.querySelectorAll('input[value="None"]').forEach(noneCheckbox => {

    noneCheckbox.addEventListener("change", function () {

        const name = this.name;
        const all = document.querySelectorAll(`input[name="${name}"]`);

        if (this.checked) {
            all.forEach(cb => {
                if (cb !== this) cb.checked = false;
            });
        } else {
            // allow others again
        }
    });

});

// If other options selected → uncheck None
document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener("change", function () {

        if (this.value !== "None" && this.checked) {
            const none = document.querySelector(`input[name="${this.name}"][value="None"]`);
            if (none) none.checked = false;
        }

    });
});