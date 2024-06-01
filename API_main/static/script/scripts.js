document.getElementById('uploadForm').addEventListener('submit', function(event) {
  event.preventDefault();
  var formData = new FormData();
  formData.append('file', document.getElementById('fileInput').files[0]);

  fetch('/api/generateDashboard', {
      method: 'POST',
      body: formData
  })
  .then(response => response.json())
  .then(data => {
      var ctx = document.getElementById('myChart').getContext('2d');
      new Chart(ctx, {
          type: 'line', // Тип графика (можно изменить на 'bar', 'pie' и т.д.)
          data: {
              labels: data.labels,
              datasets: [{
                  label: 'My Dataset',
                  data: data.values,
                  borderColor: 'rgba(75, 192, 192, 1)',
                  borderWidth: 1
              }]
          },
          options: {
              scales: {
                  y: {
                      beginAtZero: true
                  }
              }
          }
      });
  })
  .catch(error => console.error('Error:', error));
});



