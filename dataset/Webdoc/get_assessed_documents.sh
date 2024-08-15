#!/bin/bash
# Bash script, downloads the extracted_meta file containing all UUIds.
# Then, it loops through each UUID and searches for it in the extracted_meta file.

uuid_file="data/extracted_meta.csv"
assessed_uuids="../assessments/qrels.txt"
output_file="data/assessed_docs2.csv"

# check if file 'assessed_docs.csv' exists
if [ -f $output_file ]; then
    echo "File $output_file already exists. Exiting..."
    exit 1
fi
# check if file 'extracted_meta.csv' exists
if [ ! -f $uuid_file ]; then
    echo "File extracted_meta.csv does not exist. Starting download..."
    curl https://www.dropbox.com/s/1fsfwmmiea23n5z/extracted_meta.csv?dl=0 -o $uuid_file
else
    echo "File $uuid_file exists. Skipping download..."
fi

# Copy first line from uuid_file to output_file
head -n 1 "$uuid_file" > "$output_file"

# Read all values from the third column of the qrels into an array
values=($(awk -F '\t' '{print $3}' "$assessed_uuids"))

# Print number of unique values in the array
echo "Number of unique values: ${#values[@]}"
sleep 5
# Get the length of the array
len=${#values[@]}

# Get the start time
start_time=$(date +%s)
i=0
# Loop through each value in the array
for value in "${values[@]}"; do
    # Check if value already exists in output file
    if grep -q "$value" "$output_file"; then
        # If it does, skip this iteration
        continue
    fi
    # Search for lines containing the value in uuid_file and write them to output_file
    grep "$value" "$uuid_file" >> "$output_file"

    # Every 10 iterations, print the time elapsed
    if ((++i % 10 == 0)); then
        clear
        # Get the current time
        current_time=$(date +%s)

        # Calculate the elapsed time
        elapsed_time=$((current_time - start_time))

        # Calculate the average time per iteration. The result will be smaller than 1, so we need to use bc to do floating point division
        average_time_per_iteration=$(echo "scale=2; $elapsed_time / $i" | bc)

        # Calculate the total time using the average time per iteration using bc
        total_time=$(echo "scale=2; $average_time_per_iteration * $len" | bc)
        # Calculate the estimated time remaining using bc
        estimated_time_remaining=$(echo "scale=2; $total_time - $elapsed_time" | bc)

        # Convert times to HH:MM:SS format
        elapsed_time=$(date -u -d @"$elapsed_time" +'%H:%M:%S')
        estimated_time_remaining=$(date -u -d @"$estimated_time_remaining" +'%H:%M:%S')

        # Print number of iterations completed
        echo "UUIDs completed: $i/$len in $elapsed_time"
        echo "Average time per iteration: $average_time_per_iteration"
        # Print the estimated time remaining
        echo "Estimated time remaining (HH:MM:SS): $estimated_time_remaining"
        # Print a blank line
        echo
    fi


done