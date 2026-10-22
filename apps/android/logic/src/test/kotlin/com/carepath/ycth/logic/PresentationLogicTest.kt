package com.carepath.ycth.logic

import org.junit.Assert.assertEquals
import org.junit.Test

class PresentationLogicTest {
    @Test
    fun `task state marks overdue pending task`() {
        assertEquals("已逾期", formatTaskState("PENDING", true))
    }

    @Test
    fun `completion rate handles empty and mixed task lists`() {
        assertEquals(0, completionRate(emptyList()))
        assertEquals(50, completionRate(listOf("COMPLETED", "PENDING")))
    }
}
