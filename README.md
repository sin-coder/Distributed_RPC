## 用Python构建分布式高并发的RPC框架

------

### 一、为什么要写一个RPC框架？

> + 不是想要造轮子，Dubbo、gRPC、Thift这些轮子已经非常好用了

> + RPC在微服务、分布式系统、Web服务器方面应用太广泛了，需要对底层通信过程有基本认识

> + Nignx、Hadoop、K8s、Tensorflow等系统或软件的底层源码大多是关于RPC的

> + 可以更加熟悉地使用已有的RPC框架，甚至考虑如何优化已有的框架

### 二、为什么要用Python来写？

> + 一个高性能的RPC框架是不可能使用Python来完成的，Python的速度太感人了

> + 以学习基本原理为目的时，不必在乎过多细节，Python封装好的类库屏蔽掉很多细节

> + 实现同样的功能，Python的代码量相较于C/C++要少很多，减少编程难度

### 三、这个是原创的吗？

> + 永远站在巨人的肩膀之上，学习他人的代码，消化吸收，据为己用

### 四、划重点

> + 分布式和高并发是如何实现的？Prefork异步模型+Zookeeper服务发现

### 五、提供了什么RPC服务？

> + 客户端请求服务端计算一个整数值的斐波那契数列值，当然也可以自行定义

### 六、项目的组成部分

1. [源程序文件](https://github.com/sin-coder/Distributed_RPC/tree/master/Source%20Files)：在Source Files中有两个文件，server.py和client.py，具体如何使用请看部署和测试模块
2. [使用模块简介](https://github.com/sin-coder/Distributed_RPC/blob/master/%E6%A8%A1%E5%9D%97%E4%BD%BF%E7%94%A8%E7%AE%80%E4%BB%8B.md)：Socket、asyncore、json、struct、kazoo等类库，具体请看模块简介文件
3. [系统架构图](https://github.com/sin-coder/Distributed_RPC/blob/master/%E7%B3%BB%E7%BB%9F%E6%9E%B6%E6%9E%84%E5%9B%BE.md)：客户端、服务端、分布式数据库整体的工作流程图
4. [部署和测试](https://github.com/sin-coder/Distributed_RPC/blob/master/%E9%83%A8%E7%BD%B2%E5%92%8C%E6%B5%8B%E8%AF%95.md)：组件的安装，文件的执行、典型场景下的测试
5. [遇到的问题](https://github.com/sin-coder/Distributed_RPC/blob/master/%E9%81%87%E5%88%B0%E7%9A%84%E9%97%AE%E9%A2%98.md)：Windows对一些进程管理模块不支持、Zookeeper数据库的安装等
6. 改进方向：对已有的服务节点基于权重策略进行选择（负载均衡）、搭建Zookeeper集群等