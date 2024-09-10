<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $host = "rpi-all-events-cal-rpi-calendar.l.aivencloud.com";
    $port = "20044";
    $dbname = "defaultdb";
    $user = "avnadmin";
    $password = "your_actual_password_here";
    // Create connection string
    $conn_string = "host=rpi-all-events-cal-rpi-calendar.l.aivencloud.com port=20044 dbname=defaultdb user=avnadmin password=";

    

    // Create connection string
    //$conn_string = "host=$host port=$port dbname=$dbname user=$user password=$password";

    // Create connection
    $conn = pg_connect($conn_string);

    // Check connection
    if (!$conn) {
        die("Connection failed: " . pg_last_error());
    }

    // Determine the search date
    if (isset($_POST['today'])) {
        $search_date = date('Y-m-d');
    } else {
        $search_date = $_POST['search_date'];
    }

    // Prepare and execute the query
    $query = "SELECT * FROM your_table WHERE DATE(event_start) = $1";
    $result = pg_query_params($conn, $query, array($search_date));

    if (!$result) {
        die("Error in SQL query: " . pg_last_error());
    }

    // Display results
    if (pg_num_rows($result) > 0) {
        echo "<h2>Results for " . htmlspecialchars($search_date) . "</h2>";
        echo "<table>";
        echo "<tr><th>ID</th><th>Date</th><th>Other Column</th></tr>";
        while ($row = pg_fetch_assoc($result)) {
            echo "<tr>";
            echo "<td>" . htmlspecialchars($row["event_id"]) . "</td>";
            echo "<td>" . htmlspecialchars($row["event_start"]) . "</td>";
            echo "<td>" . htmlspecialchars($row["event_name"]) . "</td>";
            echo "</tr>";
        }
        echo "</table>";
    } else {
        echo "<p>No results found for " . htmlspecialchars($search_date) . "</p>";
    }

    pg_free_result($result);
    pg_close($conn);
}
?>