public class App {
    public static void main(String[] args) throws Exception {
        System.out.println("Raw Data:");
        String rawData = "  apple  \n\nbanana\n  apple \n orange\n\n";
        System.out.println("'" + rawData + "'");
        
        System.out.println("------------------------------------------------");

        System.out.println("Cleaned Data:");
        String cleaned = DataCleaner.cleanData(rawData);
        System.out.println("'" + cleaned + "'");
    }
}
