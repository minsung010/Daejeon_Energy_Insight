document.addEventListener("DOMContentLoaded", function () {
    if (window.modalInitialized) return;
    window.modalInitialized = true;

    document.addEventListener("click", function(event) {
        const modals = [
            { modal: document.getElementById('year-modal-container'), btn: document.getElementById('open-year-modal-btn'), key: 'year' },
            { modal: document.getElementById('gu-modal-container'), btn: document.getElementById('open-gu-modal-btn'), key: 'gu' },
            { modal: document.getElementById('dong-modal-container'), btn: document.getElementById('open-dong-modal-btn'), key: 'dong' },
        ];

        modals.forEach(({modal, btn, key}) => {
            if (!modal || !btn) return;

            const isOpen = getComputedStyle(modal).display !== 'none';
            const clickedInside =
                modal.contains(event.target) ||
                btn.contains(event.target);

            if (isOpen && !clickedInside) {
                const store = document.getElementById(`close-${key}-modal-btn`);
                store.click();
            }
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {

    const modals = [
        { modalId: 'year-modal-container', boxId: 'year-modal-box', openBtnId: 'open-year-modal-btn', closeBtnId: 'close-year-modal-btn' },
        { modalId: 'gu-modal-container', boxId: 'gu-modal-box', openBtnId: 'open-gu-modal-btn', closeBtnId: 'close-gu-modal-btn' },
        { modalId: 'dong-modal-container', boxId: 'dong-modal-box', openBtnId: 'open-dong-modal-btn', closeBtnId: 'close-dong-modal-btn' },
    ];

    modals.forEach(({modalId, boxId, openBtnId, closeBtnId}) => {
        const modal = document.getElementById(modalId);
        const box = document.getElementById(boxId);
        const openBtn = document.getElementById(openBtnId);
        const closeBtn = document.getElementById(closeBtnId);

        if (!modal || !box || !openBtn || !closeBtn) return;

        // 열기
        openBtn.onclick = () => {
            modal.style.display = 'block';
        };

        // 닫기 버튼
        closeBtn.onclick = () => closeModal(modal, box);

        // 외부 클릭
        document.addEventListener('click', (event) => {
            const clickedInside = box.contains(event.target) || openBtn.contains(event.target);
            if (modal.style.display !== 'none' && !clickedInside) {
                closeModal(modal, box);
            }
        });
    });

    function closeModal(modal, box) {
        box.classList.add('hide');
        modal.classList.add('hide');

        box.addEventListener('animationend', function handler() {
            modal.style.display = 'none';
            box.classList.remove('hide');
            modal.classList.remove('hide');
            box.removeEventListener('animationend', handler);
        });
    }

});