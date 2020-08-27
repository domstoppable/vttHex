#ifndef __LOGGER_H
#define __LOGGER_H

enum LogLevel {
	DEBUG, INFO, WARNING, ERROR, CRITICAL
};

static const char* levelNames[] = {
	"DEBUG", "INFO" , "WARNING", "ERROR", "CRITICAL"
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

		virtual void log(LogLevel level, char* msg){
		}

		void setLevel(LogLevel level){
			filterLevel = level;
		}

		void critical(char* msg){
			log(LogLevel::CRITICAL, msg);
		}

		void error(char* msg){
			log(LogLevel::ERROR, msg);
		}

		void warning(char* msg){
			log(LogLevel::WARNING, msg);
		}

		void info(char* msg){
			log(LogLevel::INFO, msg);
		}

		void debug(char* msg){
			log(LogLevel::DEBUG, msg);
		}
};

#endif
