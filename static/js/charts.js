// Utility function to fetch data from API
async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
        return []; // Return empty array in case of error
    }
}

// Render a line chart for daily visitors
async function renderDailyChart() {
    const data = await fetchData('/api/visitors/daily');
    if (data.length === 0) return; // Exit if no data

    const labels = data.map(item => item.VisitDate);
    const values = data.map(item => item.VisitorCount);

    new Chart(document.getElementById('daily-chart'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily Visitors',
                data: values,
                borderColor: 'blue',
                backgroundColor: 'lightblue',
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            }
        }
    });
}

// Render a bar chart for monthly visitors
async function renderMonthlyChart() {
    const data = await fetchData('/api/visitors/monthly');
    if (data.length === 0) return; // Exit if no data

    const labels = data.map(item => item.VisitMonth);
    const values = data.map(item => item.VisitorCount);

    new Chart(document.getElementById('monthly-chart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Monthly Visitors',
                data: values,
                backgroundColor: 'green',
                borderColor: 'darkgreen',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            }
        }
    });
}

// Render a pie chart for department visitors
async function renderDepartmentChart() {
    const data = await fetchData('/api/visitors/department');
    if (data.length === 0) return; // Exit if no data

    const labels = data.map(item => item.Department);
    const values = data.map(item => item.VisitorCount);

    new Chart(document.getElementById('department-chart'), {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            }
        }
    });
}

// Render a bar chart for visitors by employee
async function renderEmployeeChart() {
    const data = await fetchData('/api/visitors/employee');
    if (data.length === 0) return; // Exit if no data

    const labels = data.map(item => item.EmployeeName);
    const values = data.map(item => item.VisitorCount);

    new Chart(document.getElementById('employee-chart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Visitors by Employee',
                data: values,
                backgroundColor: 'purple',
                borderColor: 'darkpurple',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            }
        }
    });
}

// Render all charts
renderDailyChart();
renderMonthlyChart();
renderDepartmentChart();
renderEmployeeChart();
