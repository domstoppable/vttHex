#ifndef __LOGGER_H
#define __LOGGER_H

enum LogLevel {
	DEBUG, INFO, WARNING, ERROR, CRITICAL
};

class Logger {
	protected:
		LogLevel filterLevel = DEBUG;

		static Logger* global;

	public:
		static void setGlobal(Logger* logger){
			global = logger;
		}

		static Logger* getGlobal(){
			if(global == nullptr) global = new Logger();

			return global;
		}

		virtual void log(LogLevel level, const char* msg){
		}

		void setLevel(LogLevel level){
			filterLevel = level;
		}

		void critical(const char* msg){
			log(LogLevel::CRITICAL, msg);
		}

		void error(const char* msg){
			log(LogLevel::ERROR, msg);
		}

		void warning(const char* msg){
			log(LogLevel::WARNING, msg);
		}

		void info(const char* msg){
			log(LogLevel::INFO, msg);
		}

		void debug(const char* msg){
			log(LogLevel::DEBUG, msg);
		}

		const char* getLevelName(LogLevel level){
			switch(level){
				case DEBUG:
					return "DEBUG";
				case INFO:
					return "INFO";
				case WARNING:
					return "WARNING";
				case ERROR:
					return "ERROR";
				case CRITICAL:
					return "CRITICAL";

				default:
					return "LOG";
			}
		}
};

#endif
