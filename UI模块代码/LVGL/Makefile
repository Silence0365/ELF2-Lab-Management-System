#
# Makefile
#

CC              = aarch64-linux-gnu-gcc
CXX             = aarch64-linux-gnu-g++
LVGL_DIR_NAME   ?= lvgl
LVGL_DIR        ?= .

WARNINGS        := -Wall -Wshadow -Wundef -Wmissing-prototypes -Wno-discarded-qualifiers -Wextra -Wno-unused-function -Wno-error=strict-prototypes -Wpointer-arith \
                   -fno-strict-aliasing -Wno-error=cpp -Wuninitialized -Wmaybe-uninitialized -Wno-unused-parameter -Wno-missing-field-initializers -Wtype-limits \
                   -Wsizeof-pointer-memaccess -Wno-format-nonliteral -Wno-cast-qual -Wunreachable-code -Wno-switch-default -Wreturn-type -Wmultichar -Wformat-security \
                   -Wno-ignored-qualifiers -Wno-error=pedantic -Wno-sign-compare -Wno-error=missing-prototypes -Wdouble-promotion -Wclobbered -Wdeprecated -Wempty-body \
                   -Wshift-negative-value -Wstack-usage=2048 -Wno-unused-value -std=gnu99
CFLAGS          ?= -O3 -g0 -I$(LVGL_DIR)/ $(WARNINGS)
LDFLAGS         ?= -lm

#CFLAGS := -O0 -g -fsanitize=address -I$(LVGL_DIR)/ $(WARNINGS)
#LDFLAGS += -fsanitize=address

# 包含目录
CFLAGS += -I/home/silence/arm-sysroot/usr/local/include \
          -I/home/silence/arm-sysroot/usr/local/include/cjson \
          -I$(PWD)/includes   # 修改为绝对路径或正确的相对路径

# 库目录
LDFLAGS += -L/home/silence/arm-sysroot/usr/local/lib \
           -L/usr/aarch64-linux-gnu/lib \
           -lpaho-mqtt3c -lcjson \
           -lpthread -lrt


BIN             = lvgl_demo
BUILD_DIR       = ./build
BUILD_OBJ_DIR   = $(BUILD_DIR)/obj
BUILD_BIN_DIR   = $(BUILD_DIR)/bin

prefix          ?= /usr
bindir          ?= $(prefix)/bin

# Collect source files recursively
#CSRCS           := $(shell find src -type f -name '*.c')
#CXXSRCS         := $(shell find src -type f -name '*.cpp')
CSRCS           := $(shell find src ui -type f -name '*.c')  # 使用统一的方式定义
CXXSRCS         := $(shell find src -type f -name '*.cpp')

# Include LVGL sources
include $(LVGL_DIR)/lvgl/lvgl.mk

OBJEXT          ?= .o

COBJS           = $(CSRCS:.c=$(OBJEXT))
CXXOBJS         = $(CXXSRCS:.cpp=$(OBJEXT))
AOBJS           = $(ASRCS:.S=$(OBJEXT))

SRCS            = $(ASRCS) $(CSRCS) $(CXXSRCS)
OBJS            = $(AOBJS) $(COBJS) $(CXXOBJS)
TARGET          = $(addprefix $(BUILD_OBJ_DIR)/, $(patsubst ./%, %, $(OBJS)))

all: default

$(BUILD_OBJ_DIR)/%.o: %.c lv_conf.h
	@mkdir -p $(dir $@)
	@$(CC)  $(CFLAGS) -c $< -o $@
	@echo "CC  $<"

$(BUILD_OBJ_DIR)/%.o: %.cpp lv_conf.h
	@mkdir -p $(dir $@)
	@$(CXX)  $(CFLAGS) -c $< -o $@
	@echo "CXX $<"

$(BUILD_OBJ_DIR)/%.o: %.S lv_conf.h
	@mkdir -p $(dir $@)
	@$(CC)  $(CFLAGS) -c $< -o $@
	@echo "AS  $<"

default: $(TARGET)
	@mkdir -p $(dir $(BUILD_BIN_DIR)/)
	$(CXX) -o $(BUILD_BIN_DIR)/$(BIN) $(TARGET) $(LDFLAGS)

clean:
	rm -rf $(BUILD_DIR)

install:
	install -d $(DESTDIR)$(bindir)
	install $(BUILD_BIN_DIR)/$(BIN) $(DESTDIR)$(bindir)

uninstall:
	$(RM) -r $(addprefix $(DESTDIR)$(bindir)/,$(BIN))

