<?php

function skynet($prompt = "hello, what are you doing?") {
    // Define paths for the host and container
    $hostVolumePath = __DIR__ . "/data"; // Adjust the path as needed
    $containerVolumePath = "/usr/src/app/data";

    // Ensure the host directory exists
    if (!is_dir($hostVolumePath)) {
        mkdir($hostVolumePath, 0777, true);
    }

    // Build the Docker image (this is optional; you can trigger it if you need a fresh build each time)
    echo "Building Docker image...\n";
    exec("docker build -t my-selenium-script .", $outputBuild, $returnBuild);

    if ($returnBuild !== 0) {
        return "Error building Docker image: " . implode("\n", $outputBuild);
    }

    // Prepare the Docker run command
    echo "Running Docker container with prompt: '$prompt'...\n";
    $command = sprintf(
        'docker run --rm -v "%s:%s" my-selenium-script "%s"',
        $hostVolumePath,
        $containerVolumePath,
        escapeshellarg($prompt)
    );

    // Execute the Docker run command
    exec($command, $output, $returnVar);

    if ($returnVar !== 0) {
        return "Error running Docker container: " . implode("\n", $output);
    }

    // Return the output of the Docker container
    return implode("\n", $output);
}

// Example usage
$result = skynet(); // You can pass a custom prompt as an argument
echo $result;

?>
