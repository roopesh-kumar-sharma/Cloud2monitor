// function test_ui(){
//     console.log("kjdfhgkj")
// }


// let intervalId;

// function monitor_instance() {
//         console.log("Montoring")
//             const form = document.getElementById('monitor-form');
//             const cloudProvider = form.elements['cloud_provider'].value;
//             const formData = new FormData();
//             // Add common fields to formData
//             formData.append('cloud_provider', cloudProvider);
//             formData.append('instance_id', form.elements['instance_id'].value);

//             // Add cloud provider-specific fields to formData
//             if (cloudProvider === 'aws') {
//                 formData.append('aws_access_key', form.elements['aws_access_key'].value);
//                 formData.append('aws_secret_key', form.elements['aws_secret_key'].value);
//                 formData.append('aws_region', form.elements['aws_region'].value);
//             } else if (cloudProvider === 'azusre') {
//                 formData.append('azure_vm_id', form.elements['azure_vm_id'].value);
//                 formData.append('azure_region', form.elements['azure_region'].value);
//             } else if (cloudProvider === 'gcp') {
//                 formData.append('gcp_project_id', form.elements['gcp_project_id'].value);
//                 formData.append('gcp_instance_id', form.elements['gcp_instance_id'].value);
//             }
//             console.log("2")

//             const updateIntervalSeconds = 5;
            
//             if (intervalId) {
//                 clearInterval(intervalId);
//             }
//             console.log("3")
//             intervalId = setInterval(() => {
//                 fetch('/monitor', {
//                     method: 'POST',
//                     body: formData
//                 })
//                 .then(response => response.json())
//                 .then(data => {
//                     const resultsDiv = document.getElementById('monitor-results');
//                     resultsDiv.innerHTML = `
//                         <p>Instance ID: ${data.instance_id}</p>
//                         <p>Uptime: ${data.uptime}</p>
//                         <p>Public IP Address: ${data.public_ip_address}</p>
//                         <p>CPU Utilization: ${data.cpu_utilization}</p>
//                         <p>Memory Utilization: ${data.memory_utilization}</p>
//                     `;

//                     // Display CPU metric in a chart
//                     // displayCpuChart(data.cpu_utilization);

//                 })
//                 .catch(error => {
//                     console.error('Error:', error);
//                 });
                
//             }, updateIntervalSeconds * 1000);
//         }

//         function displayCpuChart(cpuUtilization) {
//         const options = {
//             chart: {
//                 type: 'line', // Change type to line
//                 height: '300', // Set the height of the chart
//                 width: '500',  // Set the width of the chart
//             },
//             series: [{
//                 name: 'CPU Utilization',
//                 data: [cpuUtilization.replace('%', '')], // Convert CPU utilization to numeric value
//             }],
//             xaxis: {
//                 categories: ['Current'], // Set x-axis categories, e.g., "Current"
//             },
//             yaxis: {
//                 title: {
//                     text: 'CPU Utilization (%)' // Set y-axis title
//                 }
//             },
//         };

//         const chart = new ApexCharts(document.getElementById('chart'), options);
//         chart.render();
//         }

//         // Show/hide specific fields based on selection
//         document.getElementById('cloud_provider').addEventListener('change', function() {
//             const awsFields = document.getElementById('aws-fields');
//             const azureFields = document.getElementById('azure-fields');
//             const gcpFields = document.getElementById('gcp-fields');

//             if (this.value === 'aws') {
//                 awsFields.style.display = 'block';
//                 azureFields.style.display = 'none';
//                 gcpFields.style.display = 'none';
//             } else if (this.value === 'azure') {
//                 awsFields.style.display = 'none';
//                 azureFields.style.display = 'block';
//                 gcpFields.style.display = 'none';
//             } else if (this.value === 'gcp') {
//                 awsFields.style.display = 'none';
//                 azureFields.style.display = 'none';
//                 gcpFields.style.display = 'block';
//             } else {
//                 awsFields.style.display = 'none';
//                 azureFields.style.display = 'none';
//                 gcpFields.style.display = 'none';
//             }
//         })