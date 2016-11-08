library(foreign)
require(graphics)
library(maptools)
library(fields)


#Load the appropriate rds file from the website http://www.gadm.org/version2
# There are 4 levels of granularity
G0<-readRDS("/Users/ruth/Desktop/Bangladesh R map/BGD_adm0.rds")
G1<-readRDS("/Users/ruth/Desktop/Bangladesh R map/BGD_adm1.rds")
G2<-readRDS("/Users/ruth/Desktop/Bangladesh R map/BGD_adm2.rds")
G3<-readRDS("/Users/ruth/Desktop/Bangladesh R map/BGD_adm3.rds")



#Names of the districts at different levels
G1$NAME_1<-as.factor(G1$NAME_1)
G2$NAME_2<-as.factor(G2$NAME_2)
G3$NAME_3<-as.factor(G3$NAME_3)

# This is making a table of disctricts and their values (random uniform at the moment) to be coloured. Could easily read this in from excel
values1<-as.data.frame(G1$NAME_1)
values2<-as.data.frame(G2$NAME_2)
values3<-as.data.frame(G3$NAME_3)

values1$density<-runif(length(values1[,1]),0,1)
values2$density<-runif(length(values2[,1]),0,1)
values3$density<-runif(length(values3[,1]),0,1)


# level 1 region plot------

####PNG outputs. I actually split it up as a multipanel plot so that the legend colourbar could go below.

zc <- as.matrix(seq(min(values1$density), max(values1$density), length.out=100))
mycolor1 <- two.colors(n=100, start=rgb(1,1,0,alpha=0.25), end=rgb(1,0,0,alpha=1), middle=rgb(1,0.5,0,alpha=0.6))


png(file="C:/Users/Nick/Desktop/BNG_level1.png",width=5, height=6, units="in", res=300)
layout(matrix(c(1,2), 2, 1, byrow = TRUE), heights=c(8,1), widths=c(4) )
layout.show(2) 
par(mar=c(0,0,0,0), oma=c(0,0,2,0))
plot(G1,col=rgb(1,1-values1$density,0,alpha=0.75), add=F, lwd=1, border=F)
invisible(text(getSpPPolygonsLabptSlots(G1), labels=as.character(G1$NAME_1), cex=0.75, col="black", font=1))
mtext(side=3, line=0, "Bangladesh something", cex=1.5)
par(mar=c(1.5,1,1,1))
image(zc, col=mycolor1, axes=F, xlab="", ylab="" )
mtext("Annual deaths in unders 5 year olds")
axis(1, at=seq(0,1, length.out=5),  labels=round(seq(min(values1$density),
                                                     max(values1$density),length.out=5), digits=2), las=1,  tcl=-.15, padj=-1, cex=1.5)
dev.off()


# level 2 region plot------

zc <- as.matrix(seq(min(values2$density), max(values2$density), length.out=100))
mycolor1 <- two.colors(n=100, start=rgb(1,1,0,alpha=0.25), end=rgb(1,0,0,alpha=1), middle=rgb(1,0.5,0,alpha=0.6))


png(file="C:/Users/Nick/Desktop/BNG_level2.png",width=5, height=6, units="in", res=300)
layout(matrix(c(1,2), 2, 1, byrow = TRUE), heights=c(8,1), widths=c(4) )
layout.show(2) 
par(mar=c(0,0,0,0), oma=c(0,0,2,0))
plot(G2,col=rgb(1,1-values2$density,0,alpha=0.75), add=F, lwd=1, border=F)
invisible(text(getSpPPolygonsLabptSlots(G2), labels=as.character(G2$NAME_2), cex=0.5, col="black", font=1))
mtext(side=3, line=0, "Bangladesh something", cex=1.5)
par(mar=c(1.5,1,1,1))
image(zc, col=mycolor1, axes=F, xlab="", ylab="" )
mtext("Annual deaths in unders 5 year olds")
axis(1, at=seq(0,1, length.out=5),  labels=round(seq(min(values2$density),
                                                     max(values2$density),length.out=5), digits=2), las=1,  tcl=-.15, padj=-1, cex=1.5)
dev.off()


# level 3 region plot------

zc <- as.matrix(seq(min(values3$density), max(values3$density), length.out=100))
mycolor1 <- two.colors(n=100, start=rgb(1,1,0,alpha=0.25), end=rgb(1,0,0,alpha=1), middle=rgb(1,0.5,0,alpha=0.6))


png(file="C:/Users/Nick/Desktop/BNG_level3.png",width=5, height=6, units="in", res=300)
layout(matrix(c(1,2), 2, 1, byrow = TRUE), heights=c(8,1), widths=c(4) )
layout.show(2) 
par(mar=c(0,0,0,0), oma=c(0,0,2,0))
plot(G3,col=rgb(1,1-values3$density,0,alpha=0.75), add=F, lwd=1, border=F)
#invisible(text(getSpPPolygonsLabptSlots(G3), labels=as.character(G3$NAME_3), cex=0.5, col="black", font=1))
mtext(side=3, line=0, "Bangladesh something", cex=1.5)
par(mar=c(1.5,1,1,1))
image(zc, col=mycolor1, axes=F, xlab="", ylab="" )
mtext("Annual deaths in unders 5 year olds")
axis(1, at=seq(0,1, length.out=5),  labels=round(seq(min(values3$density),
                                                     max(values3$density),length.out=5), digits=2), las=1,  tcl=-.15, padj=-1, cex=1.5)
dev.off()

