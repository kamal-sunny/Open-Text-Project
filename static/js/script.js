// ---------------- DOMContentLoaded ----------------
document.addEventListener("DOMContentLoaded", () => {
    // ----- Register Form -----
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const username = registerForm.username.value.trim();
            const password = registerForm.password.value.trim();
            const role = registerForm.role.value;

            if(username.length < 5 || password.length < 5){
                alert("Username and password must be at least 5 characters long!");
                return;
            }

            // Connect to backend via Flask (submit normally)
            registerForm.submit();
        });
    }

    // ----- Player Login -----
    const playerLogin = document.getElementById("playerLogin");
    if (playerLogin) {
        playerLogin.addEventListener("submit", (e) => {
            e.preventDefault();
            // Normally login will be checked via Flask backend
            playerLogin.submit();

            // Show game area only if login successful (handled in Flask)
            const gameArea = document.getElementById("gameArea");
            if(gameArea) gameArea.classList.remove("hidden");
        });
    }

    // ----- Admin Login -----
    const adminLogin = document.getElementById("adminLogin");
    if (adminLogin) {
        adminLogin.addEventListener("submit", (e) => {
            e.preventDefault();
            adminLogin.submit();

            const adminPanel = document.getElementById("adminPanel");
            if(adminPanel) adminPanel.classList.remove("hidden");
        });
    }

    // ----- Tile Neon Hover -----
    document.querySelectorAll('.tile').forEach(tile => {
        tile.addEventListener('mouseenter', () => {
            tile.style.boxShadow = '0 0 15px #00ff88';
        });
        tile.addEventListener('mouseleave', () => {
            tile.style.boxShadow = 'none';
        });
    });

    // ----- Tour Setup -----
    const tourBtn = document.getElementById('tour-button');
    const overlay = document.getElementById('tour-overlay');
    const tooltip = document.getElementById('tour-tooltip');
    const tourText = document.getElementById('tour-text');
    const nextBtn = document.getElementById('tour-next');
    const prevBtn = document.getElementById('tour-prev');
    const skipBtn = document.getElementById('tour-skip');

    const steps = [
        { target: '#register-link', text: 'Click here to register and create your account.' },
        { target: '#player-btn', text: 'Click here to login as a Player and start guessing words.' },
        { target: '#admin-btn', text: 'Click here to login as Admin to manage words and reports.' },
        { target: '#about-link', text: 'Click here to learn about how the game works.' }
    ];

    let currentStep = 0;

    function showStep(index) {
        const step = steps[index];
        const element = document.querySelector(step.target);
        if (!element) return;

        document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight'));
        element.classList.add('tour-highlight');

        // Scroll element into view
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Tooltip positioning
        const rect = element.getBoundingClientRect();
        let top = rect.bottom + 10;
        let left = rect.left;

        if (top + 100 > window.innerHeight) top = rect.top - 110;
        if (left + 260 > window.innerWidth) left = window.innerWidth - 270;

        tooltip.style.top = `${top}px`;
        tooltip.style.left = `${left}px`;
        tourText.innerText = step.text;

        overlay.classList.add('active');
        tooltip.classList.add('active');

        prevBtn.style.display = index === 0 ? 'none' : 'inline-block';
        nextBtn.innerText = index === steps.length - 1 ? 'Finish' : 'Next';
    }

    function hideTour() {
        overlay.classList.remove('active');
        tooltip.classList.remove('active');
        document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight'));
    }

    nextBtn.addEventListener('click', () => {
        if(currentStep < steps.length - 1) currentStep++;
        else { hideTour(); return; }
        showStep(currentStep);
    });

    prevBtn.addEventListener('click', () => {
        if(currentStep > 0) currentStep--;
        showStep(currentStep);
    });

    skipBtn.addEventListener('click', hideTour);

    tourBtn.addEventListener('click', () => {
        currentStep = 0;
        showStep(currentStep);
    });
});

// ----- Reports Placeholder -----
function getDailyReport(){
    document.getElementById("dailyReportResult").innerText = "Daily report placeholder";
}
function getUserReport(){
    document.getElementById("userReportResult").innerText = "User report placeholder";
}
