import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Scanner;
import java.util.Set;

public class DataCleaner {

    public static String cleanData(String input) {
        if (input == null || input.isEmpty()) {
            return "";
        }

        Scanner scanner = new Scanner(input);
        Set<String> uniqueLines = new LinkedHashSet<>();

        while (scanner.hasNextLine()) {
            String line = scanner.nextLine();
            // 1. Trim whitespace
            String trimmed = line.trim();

            // 2. Remove empty lines
            if (!trimmed.isEmpty()) {
                // 3. Remove duplicates (handled by Set)
                uniqueLines.add(trimmed);
            }
        }
        scanner.close();

        return String.join("\n", uniqueLines);
    }
}
