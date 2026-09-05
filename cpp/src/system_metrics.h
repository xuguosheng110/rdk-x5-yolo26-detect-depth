#pragma once

#include <cstdint>
#include <functional>
#include <mutex>
#include <optional>
#include <string>
#include <vector>

namespace system_metrics {

struct CpuTimes {
  std::uint64_t total = 0;
  std::uint64_t idle = 0;
};

std::optional<CpuTimes> ParseProcStat(const std::string& text);
std::optional<double> CpuUtilizationPercent(
    const std::optional<CpuTimes>& previous, const CpuTimes& current);
std::optional<double> ParseMeminfoUtilizationPercent(const std::string& text);

struct Metrics {
  double cpu_util_pct = 0.0;
  double memory_util_pct = 0.0;
  std::optional<double> cpu_temp_c;
  std::optional<double> ddr_temp_c;
};

class Sampler {
 public:
  using Reader =
      std::function<std::optional<std::string>(const std::string& path)>;

  Sampler();
  explicit Sampler(Reader reader, std::vector<std::string> thermal_zones = {});
  Metrics Sample();

 private:
  Reader reader_;
  std::vector<std::string> thermal_zones_;
  std::mutex mutex_;
  std::optional<CpuTimes> previous_cpu_;
  Metrics last_;
};

}  // namespace system_metrics
