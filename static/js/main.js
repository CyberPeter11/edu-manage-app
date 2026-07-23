document.addEventListener('DOMContentLoaded', () => {
    // --- Toast Notifications ---
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(120%)';
            setTimeout(() => toast.remove(), 300);
        }, 5000);

        const closeBtn = toast.querySelector('.close-toast');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            });
        }
    });

    // --- Modal Logic ---
    const modal = document.getElementById('studentModal');
    const addBtn = document.getElementById('addStudentBtn');
    const closeBtns = document.querySelectorAll('.close-modal, .close-modal-btn');
    const form = document.getElementById('studentForm');
    const modalTitle = document.getElementById('modalTitle');
    
    // Add Student
    if (addBtn) {
        addBtn.addEventListener('click', () => {
            modalTitle.textContent = 'Add New Student';
            form.reset();
            
            // Set today's date for enrollment
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('enrollment_date').value = today;
            
            // Reset action to add route
            form.action = '/students/add';
            modal.classList.add('active');
        });
    }

    // Edit Student
    const editBtns = document.querySelectorAll('.edit-student-btn');
    editBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            const studentId = btn.getAttribute('data-id');
            modalTitle.textContent = 'Edit Student';
            
            // Fetch student data
            try {
                const response = await fetch(`/api/students/${studentId}`);
                if (response.ok) {
                    const student = await response.json();
                    
                    // Populate form
                    document.getElementById('first_name').value = student.first_name;
                    document.getElementById('last_name').value = student.last_name;
                    document.getElementById('email').value = student.email;
                    document.getElementById('course').value = student.course;
                    document.getElementById('enrollment_date').value = student.enrollment_date;
                    document.getElementById('status').value = student.status;
                    
                    // Set action to edit route
                    form.action = `/students/edit/${studentId}`;
                    modal.classList.add('active');
                }
            } catch (error) {
                console.error("Error fetching student data:", error);
            }
        });
    });

    // Close Modal
    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    });

    // Close on overlay click
    if(modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    }

    // --- Live Search & Filtering ---
    const searchInput = document.getElementById('globalSearch');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const studentRows = document.querySelectorAll('.student-row');
    const noResultsState = document.getElementById('noResultsState');
    const studentsTable = document.getElementById('studentsTable');

    let currentFilter = 'All';
    let currentSearch = '';

    // Check URL parameters for initial filter (from Dashboard clicks)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('filter') && filterBtns.length > 0) {
        const urlFilter = urlParams.get('filter');
        const btn = document.querySelector(`.filter-btn[data-filter="${urlFilter}"]`);
        if (btn) {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = urlFilter;
        }
    }

    // Auto-open edit modal if URL param exists
    if (urlParams.has('edit')) {
        const editId = urlParams.get('edit');
        const editBtn = document.querySelector(`.edit-student-btn[data-id="${editId}"]`);
        if (editBtn) {
            editBtn.click();
            // clean up URL so refreshing doesn't keep opening modal
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    function applyFilters() {
        if (!studentRows.length) return;
        
        let visibleCount = 0;
        
        studentRows.forEach(row => {
            const status = row.getAttribute('data-status');
            const searchData = row.getAttribute('data-search') || '';
            
            const matchesFilter = currentFilter === 'All' || status === currentFilter;
            const matchesSearch = searchData.includes(currentSearch.toLowerCase());
            
            if (matchesFilter && matchesSearch) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        if (noResultsState && studentsTable) {
            if (visibleCount === 0) {
                studentsTable.style.display = 'none';
                noResultsState.style.display = 'flex';
            } else {
                studentsTable.style.display = 'table';
                noResultsState.style.display = 'none';
            }
        }
    }

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            currentSearch = e.target.value.trim();
            // If on dashboard, redirect to students page with search query?
            // For now, if there are no studentRows, maybe we are on the dashboard.
            if (!studentRows.length) {
                window.location.href = `/students?search=${encodeURIComponent(currentSearch)}`;
            } else {
                applyFilters();
            }
        });
    }

    if (urlParams.has('search') && searchInput) {
        currentSearch = urlParams.get('search');
        searchInput.value = currentSearch;
        // Clean url
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    if (filterBtns) {
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.getAttribute('data-filter');
                applyFilters();
            });
        });
    }
    
    // Apply initial filters on load
    applyFilters();

    // --- Coming Soon Toasts ---
    const comingSoonLinks = document.querySelectorAll('.coming-soon');
    const toastContainer = document.getElementById('toastContainer');
    
    comingSoonLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            if (toastContainer) {
                const toast = document.createElement('div');
                toast.className = 'toast toast-warning';
                toast.innerHTML = `
                    <i class="fa-solid fa-rocket"></i>
                    <span>This feature is coming soon!</span>
                    <button class="close-toast"><i class="fa-solid fa-times"></i></button>
                `;
                
                toastContainer.appendChild(toast);
                
                setTimeout(() => {
                    toast.style.opacity = '0';
                    toast.style.transform = 'translateX(120%)';
                    setTimeout(() => toast.remove(), 300);
                }, 4000);
                
                const closeBtn = toast.querySelector('.close-toast');
                if (closeBtn) {
                    closeBtn.addEventListener('click', () => {
                        toast.style.opacity = '0';
                        setTimeout(() => toast.remove(), 300);
                    });
                }
            }
        });
    });

    // --- Quick Edit Row Click ---
    const quickEditRows = document.querySelectorAll('.quick-edit-row');
    quickEditRows.forEach(row => {
        row.addEventListener('click', (e) => {
            if (e.target.closest('button') || e.target.closest('a')) return;
            const studentId = row.getAttribute('data-id');
            window.location.href = `/students?edit=${studentId}`;
        });
    });
});
